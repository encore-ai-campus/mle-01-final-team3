"""실행(review_runs) 만들기·실패 처리·시간 초과·Agent 작업 내용 만들기. 설계서 3장 '실행 상태'.

QUEUED → (Agent가 202로 접수) RUNNING → (완료 통지) SUCCEEDED / FAILED
QUEUED → (작업 요청 3번 실패) FAILED / AGENT_UNAVAILABLE
QUEUED·RUNNING → (실행을 만든 뒤 180초) FAILED / RUN_TIMEOUT

시간 초과는 주기 작업 없이, 실행·검토 건을 읽거나 완료 통지를 받을 때 확인해서 확정한다.
상태는 API로만 보이므로 결과는 같다.
- 실행 하나를 볼 때: expire_if_timed_out(db, run)
- 목록·대시보드처럼 여러 건을 볼 때: 조회 전에 expire_overdue_runs(db) 한 번
"""

from datetime import timedelta

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.ids import new_id
from app.core.security import utcnow
from app.models import Attachment, Review, ReviewAttachment, ReviewRun
from app.reviews import codes as C
from app.reviews.attachments import signed_url
from app.reviews.state import current_report, latest_legal, report_view

TIMEOUT_MESSAGE = "검토 시간이 초과되었습니다. 다시 검토해 주세요."
UNAVAILABLE_MESSAGE = "AI 검토 서버에 연결하지 못했습니다. 다시 검토해 주세요."


def create_run(
    db: DbSession,
    review: Review,
    stage: str,
    background: BackgroundTasks,
    *,
    retry_of: ReviewRun | None = None,
) -> ReviewRun:
    """새 실행을 QUEUED로 만들고, 응답을 보낸 뒤 Agent에 작업을 요청하도록 예약한다. commit은 호출한 쪽에서."""
    from app.agent.dispatch import dispatch_run  # 순환 import 방지

    now = utcnow()
    run = ReviewRun(
        id=new_id(db, "run"),
        review_id=review.id,
        stage=stage,
        status=C.QUEUED,
        attempt=(retry_of.attempt or 1) + 1 if retry_of else 1,
        retry_of=retry_of.id if retry_of else None,
        created_at=now,
        updated_at=now,
    )
    db.add(run)
    review.updated_at = now
    background.add_task(dispatch_run, run.id)
    return run


def fail_run(db: DbSession, run: ReviewRun, code: str, message: str, retryable: bool) -> None:
    """실행을 FAILED로 확정한다. 보고서는 그대로 둔다."""
    now = utcnow()
    run.status = C.FAILED
    run.error_code, run.error_message, run.error_retryable = code, message[:500], retryable
    run.finished_at = run.updated_at = now
    review = db.get(Review, run.review_id)
    if review is not None:
        review.updated_at = now


def expire_if_timed_out(db: DbSession, run: ReviewRun | None) -> bool:
    """실행을 만든 뒤 180초가 지나도 끝나지 않았으면 FAILED / RUN_TIMEOUT으로 확정한다. commit은 호출한 쪽에서."""
    if run is None or run.status not in C.ACTIVE:
        return False
    deadline = timedelta(seconds=settings.run_timeout_seconds)
    if utcnow() - run.created_at < deadline:
        return False
    db.refresh(run, with_for_update=True)  # 완료 통지와 동시에 처리되지 않도록 잠그고 다시 확인
    if run.status not in C.ACTIVE:
        return False
    fail_run(db, run, C.RUN_TIMEOUT, TIMEOUT_MESSAGE, True)
    return True


def expire_overdue_runs(db: DbSession, review_ids: list[str] | None = None) -> int:
    """목록·대시보드용. 180초가 지난 QUEUED·RUNNING 실행을 한꺼번에 FAILED / RUN_TIMEOUT으로 확정한다.

    목록을 조회하기 전에 한 번 부른다. review_ids를 주면 그 검토 건들만 본다. commit은 호출한 쪽에서.
    완료 통지가 처리 중이라 잠긴 실행은 건너뛴다 (완료 통지 쪽에서 시간 초과를 직접 확인한다).
    """
    deadline = utcnow() - timedelta(seconds=settings.run_timeout_seconds)
    stmt = select(ReviewRun).where(ReviewRun.status.in_(list(C.ACTIVE)), ReviewRun.created_at <= deadline)
    if review_ids is not None:
        stmt = stmt.where(ReviewRun.review_id.in_(review_ids))
    runs = db.scalars(stmt.with_for_update(skip_locked=True)).all()
    for run in runs:
        fail_run(db, run, C.RUN_TIMEOUT, TIMEOUT_MESSAGE, True)
    return len(runs)


def first_run(db: DbSession, run: ReviewRun) -> ReviewRun:
    """재시도 사슬(retry_of)을 따라 최초 실행을 찾는다."""
    while run.retry_of:
        run = db.get(ReviewRun, run.retry_of)
    return run


def run_input_text(db: DbSession, run: ReviewRun, review: Review) -> str:
    """이 실행이 심의할 문구.

    - AI_SCREENING·RA_SUGGEST: 처음 입력한 원문
    - RA_RECHECK: 마케팅 담당자가 [재심의]한 추천 문구. 재시도해도 같은 문구 (설계서 6장)

    review_runs에 입력 문구 칼럼이 아직 없어서, 최초 RA_RECHECK 실행 직전에 [재심의] 처리된 RA_SUGGEST 실행의
    suggestion.text를 쓴다. 검토 건당 활성 실행은 하나라 순서가 섞이지 않는다.
    칼럼(review_runs.input_text)은 추가하기로 합의했다. 인증·공통 기반 담당이 추가하면 그 값을 쓰도록 바꾼다.
    """
    if run.stage != C.RA_RECHECK:
        return review.text
    root = first_run(db, run)
    source = db.scalars(
        select(ReviewRun)
        .where(
            ReviewRun.review_id == review.id,
            ReviewRun.stage == C.RA_SUGGEST,
            ReviewRun.created_at <= root.created_at,
            ReviewRun.suggestion["status"].astext == C.SUGGESTION_RECHECKED,
        )
        .order_by(ReviewRun.created_at.desc())
        .limit(1)
    ).first()
    if source is None:  # 정상 흐름에서는 생기지 않는다
        raise RuntimeError(f"재심의 문구를 찾을 수 없습니다: {run.id}")
    return source.suggestion["text"]


def build_job(db: DbSession, run: ReviewRun) -> dict:
    """백엔드 → Agent 작업 요청 본문. POST {AGENT_URL}/internal/v1/review-jobs (설계서 6장 '연동 방향')."""
    review = db.get(Review, run.review_id)
    attachments = db.execute(
        select(Attachment)
        .join(ReviewAttachment, ReviewAttachment.attachment_id == Attachment.id)
        .where(ReviewAttachment.review_id == review.id)
        .order_by(Attachment.id)
    ).scalars()

    base = current_report(db, review.id) if run.stage in (C.RA_SUGGEST, C.RA_RECHECK) else None
    legal_opinion = None
    if run.stage == C.RA_SUGGEST and base is not None:
        legal = latest_legal(db, review.id)
        if legal is not None and legal.report_run_id == base.run_id and legal.status == C.OPINION_SENT:
            legal_opinion = legal.reason

    return {
        "schemaVersion": "1.0",
        "runId": run.id,
        "reviewId": review.id,
        "stage": run.stage,
        "title": review.title,
        "productCategory": review.product_category,
        "text": run_input_text(db, run, review),
        "attachments": [
            {"attachmentId": a.id, "filename": a.filename, "url": signed_url(a.id)} for a in attachments
        ],
        "baseReportRunId": base.run_id if base else None,
        "baseReport": report_view(base) if base else None,
        "legalOpinion": legal_opinion,
    }
