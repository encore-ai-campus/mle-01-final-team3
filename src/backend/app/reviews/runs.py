"""실행(review_runs) 만들기·실패 처리·시간 초과·Agent 작업 내용 만들기. 설계서 3장 '실행 상태'.

QUEUED → (Agent가 202·200으로 접수) RUNNING → (완료 통지) SUCCEEDED / FAILED
QUEUED → (작업 요청 3번 실패) FAILED / AGENT_UNAVAILABLE
QUEUED·RUNNING → (실행을 만든 뒤 180초) FAILED / RUN_TIMEOUT

시간 초과는 주기 작업 없이, 실행·검토 건을 읽거나 완료 통지를 받을 때 확인해서 확정한다.
상태는 API로만 보이므로 결과는 같다.
- 실행 하나를 볼 때: expire_if_timed_out(db, run)
- 목록·대시보드처럼 여러 건을 볼 때: 조회 전에 expire_overdue_runs(db) 한 번

잠금 순서 (설계서 3장): users → reviews → review_runs. 실행을 바꾸면 reviews.updated_at도 바뀌므로,
실행 행을 잠그기 전에 그 검토 건 행을 먼저 잠근다. 순서가 엇갈리면 두 요청이 서로를 기다리는 교착이 생긴다.
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
from app.reviews.state import current_report, latest_legal, report_of_version, report_view

TIMEOUT_MESSAGE = "검토 시간이 초과되었습니다. 다시 검토해 주세요."
UNAVAILABLE_MESSAGE = "AI 검토 서버에 연결하지 못했습니다. 다시 검토해 주세요."


def create_run(
    db: DbSession,
    review: Review,
    stage: str,
    background: BackgroundTasks,
    *,
    retry_of: ReviewRun | None = None,
    input_text: str | None = None,
) -> ReviewRun:
    """새 실행을 QUEUED로 만들고, 응답을 보낸 뒤 Agent에 작업을 요청하도록 예약한다. commit은 호출한 쪽에서.

    input_text: 재심의(RA_RECHECK)할 추천 문구. 재시도는 원래 실행의 값을 그대로 복사한다.
    """
    from app.agent.dispatch import dispatch_run  # 순환 import 방지

    now = utcnow()
    run = ReviewRun(
        id=new_id(db, "run"),
        review_id=review.id,
        stage=stage,
        status=C.QUEUED,
        attempt=(retry_of.attempt or 1) + 1 if retry_of else 1,
        retry_of=retry_of.id if retry_of else None,
        input_text=retry_of.input_text if retry_of else input_text,
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


def lock_review_then_run(db: DbSession, run_id: str) -> ReviewRun | None:
    """잠금 순서대로 실행의 검토 건 행을 먼저 잠그고, 그다음 실행 행을 잠가 최신 값으로 읽는다. 없는 실행이면 None."""
    run = db.get(ReviewRun, run_id)
    if run is None:
        return None
    db.get(Review, run.review_id, with_for_update=True)
    return db.get(ReviewRun, run_id, with_for_update=True, populate_existing=True)


def expire_if_timed_out(db: DbSession, run: ReviewRun | None) -> bool:
    """실행을 만든 뒤 180초가 지나도 끝나지 않았으면 FAILED / RUN_TIMEOUT으로 확정한다. commit은 호출한 쪽에서."""
    if run is None or run.status not in C.ACTIVE:
        return False
    deadline = timedelta(seconds=settings.run_timeout_seconds)
    if utcnow() - run.created_at < deadline:
        return False
    # 완료 통지와 동시에 처리되지 않도록 잠그고 다시 확인한다. 검토 건 → 실행 순서 (호출한 쪽이 이미 잠갔으면 그대로)
    db.get(Review, run.review_id, with_for_update=True)
    db.refresh(run, with_for_update=True)
    if run.status not in C.ACTIVE:
        return False
    fail_run(db, run, C.RUN_TIMEOUT, TIMEOUT_MESSAGE, True)
    return True


def expire_overdue_runs(db: DbSession, review_ids: list[str] | None = None) -> int:
    """목록·대시보드용. 180초가 지난 QUEUED·RUNNING 실행을 한꺼번에 FAILED / RUN_TIMEOUT으로 확정한다.

    목록을 조회하기 전에 한 번 부른다. review_ids를 주면 그 검토 건들만 본다. commit은 호출한 쪽에서.
    다른 요청이 처리 중이라 잠긴 검토 건은 기다리지 않고 건너뛴다 (그 요청이 시간 초과를 직접 확인한다).
    """
    deadline = utcnow() - timedelta(seconds=settings.run_timeout_seconds)
    overdue = (ReviewRun.status.in_(list(C.ACTIVE)), ReviewRun.created_at <= deadline)
    stmt = select(ReviewRun.review_id).where(*overdue).distinct()
    if review_ids is not None:
        stmt = stmt.where(ReviewRun.review_id.in_(review_ids))
    candidates = db.scalars(stmt).all()
    if not candidates:
        return 0
    # 검토 건 → 실행 순서로 잠근다. 실행도 잠근 뒤 다시 조건을 확인한다 (그사이 완료 통지가 처리됐을 수 있음)
    locked = db.scalars(select(Review.id).where(Review.id.in_(candidates)).with_for_update(skip_locked=True)).all()
    if not locked:
        return 0
    runs = db.scalars(
        select(ReviewRun)
        .where(ReviewRun.review_id.in_(locked), *overdue)
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    ).all()
    for run in runs:
        fail_run(db, run, C.RUN_TIMEOUT, TIMEOUT_MESSAGE, True)
    return len(runs)


def run_input_text(run: ReviewRun, review: Review) -> str:
    """이 실행이 심의할 문구. AI 심의·추천 문구 생성은 처음 입력한 원문, 재심의는 [재심의]한 추천 문구(input_text)."""
    if run.stage == C.RA_RECHECK:
        return run.input_text
    return review.text


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
    initial = None  # RA_SUGGEST: 최초 AI 심의 보고서(v1). 최신이 v1이면 baseReport와 같으므로 null
    if run.stage == C.RA_SUGGEST and base is not None:
        legal = latest_legal(db, review.id)
        if legal is not None and legal.report_run_id == base.run_id and legal.status == C.OPINION_SENT:
            legal_opinion = legal.reason
        if base.version > 1:
            initial = report_of_version(db, review.id, 1)

    return {
        "schemaVersion": "1.0",
        "runId": run.id,
        "reviewId": review.id,
        "stage": run.stage,
        "title": review.title,
        "productCategory": review.product_category,
        "channel": review.channel,
        "mainIngredients": review.main_ingredients or [],
        "text": run_input_text(run, review),
        "attachments": [
            {"attachmentId": a.id, "filename": a.filename, "url": signed_url(a.id)} for a in attachments
        ],
        "baseReportRunId": base.run_id if base else None,
        "baseReport": report_view(base) if base else None,
        "initialReport": report_view(initial) if initial else None,
        "legalOpinion": legal_opinion,
    }
