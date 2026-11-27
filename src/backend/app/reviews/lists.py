"""검토함 목록 API. 설계서 5장 '마케팅팀 검토함과 전송 내역'·'법무팀 검토함'.

GET /reviews?view=ALL      마케팅 '검토함'(M-41). 검토 건당 1행
GET /reviews?view=SENT     마케팅 '법무팀 전송 내역'(M-50). 법무 검토 요청 건당 1행
GET /legal-submissions     법무 '검토함'. 요청 건당 1행

단계·결과·법무 상태·버튼은 DB에 저장하지 않고 계산하는 값이라(state.py), 목록은 파이썬에서 계산·필터한 뒤
memory_page로 자른다. 대시보드 할 일 카드도 같은 함수(review_rows·legal_rows)로 세어 목록과 건수가 같다.
조회 전에 180초가 지난 실행을 먼저 확정한다(expire_overdue_runs).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.deps import Lawyer, Marketer, get_db
from app.core.pagination import memory_page
from app.core.security import utcnow
from app.core.times import KST, to_kst
from app.models import LegalSubmission, Report, Review, ReviewRun, User
from app.reviews import codes as C
from app.reviews.runs import expire_overdue_runs
from app.reviews.state import base_actions, user_ref

router = APIRouter()

LEGAL_REVIEW = "LEGAL_REVIEW"  # 목록 전용 단계: 최신 보고서로 법무 검토를 요청한 건
NOT_SENT = "NOT_SENT"
PENDING, IN_REVIEW = "PENDING", "IN_REVIEW"
START_LEGAL_REVIEW, SEND_OPINION = "START_LEGAL_REVIEW", "SEND_OPINION"

ProductCategory = Literal["HEALTH_FUNCTIONAL_FOOD", "GENERAL_FOOD", "CHILDREN_PREFERRED_FOOD"]
Stage = Literal["AI_SCREENING", "RA_SUGGEST", "RA_RECHECK", "LEGAL_REVIEW"]
Result = Literal["SUITABLE", "UNSUITABLE", "LEGAL_OPINION_SENT", "ENDED", "PUBLISHED", "CANCELED"]
Decision = Literal["SUITABLE", "UNSUITABLE"]
LegalStatus = Literal["NOT_SENT", "PENDING", "IN_REVIEW", "OPINION_SENT"]
SubmissionStatus = Literal["PENDING", "IN_REVIEW", "OPINION_SENT"]
Action = Literal[
    "RUN_RA", "RETRY_RUN", "SEND_TO_LEGAL", "END", "PUBLISH", "CANCEL", "RECHECK_SUGGESTION", "DISMISS_SUGGESTION"
]
Limit = Annotated[int, Query(ge=1, le=100)]


# ---------- 한 번에 읽기 ----------


@dataclass
class Snapshot:
    """목록 계산에 필요한 행을 한 번에 읽어 둔 것 (검토 건마다 쿼리하지 않으려고)."""

    reviews: list[Review]
    users: dict[str, User]
    latest_run: dict[str, ReviewRun] = field(default_factory=dict)  # 검토 건별 가장 최근 실행
    current_report: dict[str, Report] = field(default_factory=dict)  # 검토 건별 최신 보고서
    reports: dict[str, Report] = field(default_factory=dict)  # run_id → 보고서
    legal: list[LegalSubmission] = field(default_factory=list)
    latest_legal: dict[str, LegalSubmission] = field(default_factory=dict)  # 검토 건별 가장 최근 요청
    ra_runs: list[ReviewRun] = field(default_factory=list)  # AI 추천 요청(RA_SUGGEST·RA_RECHECK) 실행 (대시보드 집계용)


def load_snapshot(db: DbSession) -> Snapshot:
    expire_overdue_runs(db)
    db.flush()
    snap = Snapshot(
        reviews=list(db.scalars(select(Review)).all()),
        users={u.id: u for u in db.scalars(select(User)).all()},
    )
    for run in db.scalars(select(ReviewRun).order_by(ReviewRun.created_at, ReviewRun.id)).all():
        snap.latest_run[run.review_id] = run  # 뒤에 온 것(최근)이 남는다
        if run.stage in (C.RA_SUGGEST, C.RA_RECHECK):
            snap.ra_runs.append(run)
    for rep in db.scalars(select(Report).order_by(Report.version)).all():
        snap.reports[rep.run_id] = rep
        snap.current_report[rep.review_id] = rep
    snap.legal = list(db.scalars(select(LegalSubmission).order_by(LegalSubmission.sent_at, LegalSubmission.id)).all())
    for sub in snap.legal:
        snap.latest_legal[sub.review_id] = sub
    return snap


# ---------- 마케팅 행 ----------


@dataclass
class Row:
    data: dict  # 응답 1행
    sort_at: datetime  # 정렬 시각 (UTC 원본)
    row_id: str  # 정렬값이 같을 때 쓰는 행 ID
    author_id: str | None = None

    def key(self) -> tuple[datetime, str]:
        return (self.sort_at, self.row_id)


def _legal_status(report: Report | None, legal: LegalSubmission | None) -> str | None:
    """최신 보고서 기준 법무 상태. 그 보고서로 요청했으면 요청 상태, 적합인데 요청 안 했으면 NOT_SENT, 부적합·보고서 없음은 null."""
    if report is None:
        return None
    if legal is not None and legal.report_run_id == report.run_id:
        return legal.status
    return NOT_SENT if report.decision == C.SUITABLE else None


def review_rows(snap: Snapshot, user: User) -> list[Row]:
    """view=ALL: 검토 건당 1행. 판정·단계는 최신 보고서 기준, 보고서가 없으면 실행 단계."""
    rows = []
    for review in snap.reviews:
        run = snap.latest_run.get(review.id)
        report = snap.current_report.get(review.id)
        latest = snap.latest_legal.get(review.id)
        legal = latest if (report and latest and latest.report_run_id == report.run_id) else None

        if legal is not None:
            stage = LEGAL_REVIEW
        elif report is not None:
            stage = report.stage
        else:
            stage = run.stage if run else None

        if review.closed_type:
            result = review.closed_type
        elif legal is not None and legal.status == C.OPINION_SENT:
            result = "LEGAL_OPINION_SENT"
        else:
            result = report.decision if report else None

        actions = base_actions(review, run, report, latest) if review.author_id == user.id else []
        rows.append(Row(
            data={
                "reviewId": review.id,
                "title": review.title,
                "version": report.version if report else None,
                "productCategory": review.product_category,
                "author": user_ref(snap.users.get(review.author_id)),
                "stage": stage,
                "decision": report.decision if report else None,
                "result": result,
                "runStatus": run.status if run else None,
                "latestRunId": run.id if run else None,
                "reportRunId": report.run_id if report else None,
                "legalStatus": _legal_status(report, latest),
                "submissionId": legal.id if legal else None,
                "closeType": review.closed_type,
                "createdAt": to_kst(review.created_at),
                "updatedAt": to_kst(review.updated_at),
                "sentAt": to_kst(legal.sent_at) if legal else None,
                "decidedAt": to_kst(legal.decided_at) if legal else None,
                "closedAt": to_kst(review.closed_at),
                "allowedActions": actions,
            },
            sort_at=review.updated_at or review.created_at,
            row_id=review.id,
            author_id=review.author_id,
        ))  # fmt: skip
    return rows


def sent_rows(snap: Snapshot, user: User) -> list[Row]:
    """view=SENT: 법무 검토 요청 건당 1행. 판정·단계·버전·보고서 ID는 요청 시점(요청한 보고서) 기준, 법무 상태는 현재 값.

    버튼은 그 요청이 검토 건의 최신 보고서로 한 요청일 때만 준다. 재심의로 새 보고서가 나온 뒤의 예전 요청 행은 [].
    """
    reviews = {r.id: r for r in snap.reviews}
    rows = []
    for sub in snap.legal:
        review = reviews.get(sub.review_id)
        if review is None:
            continue
        report = snap.reports.get(sub.report_run_id)
        run = snap.latest_run.get(review.id)
        current = snap.current_report.get(review.id)
        is_current = current is not None and current.run_id == sub.report_run_id
        actions = []
        if is_current and review.author_id == user.id:
            actions = base_actions(review, run, current, snap.latest_legal.get(review.id))
        if sub.status == C.OPINION_SENT:
            result = "LEGAL_OPINION_SENT"
        else:
            result = report.decision if report else None
        if is_current and review.closed_type:
            result = review.closed_type
        rows.append(Row(
            data={
                "reviewId": review.id,
                "title": review.title,
                "version": report.version if report else None,
                "productCategory": review.product_category,
                "author": user_ref(snap.users.get(review.author_id)),
                "stage": report.stage if report else None,
                "decision": report.decision if report else None,
                "result": result,
                "runStatus": run.status if run else None,
                "latestRunId": run.id if run else None,
                "reportRunId": sub.report_run_id,
                "legalStatus": sub.status,
                "submissionId": sub.id,
                "closeType": review.closed_type,
                "createdAt": to_kst(review.created_at),
                "updatedAt": to_kst(review.updated_at),
                "sentAt": to_kst(sub.sent_at),
                "decidedAt": to_kst(sub.decided_at),
                "closedAt": to_kst(review.closed_at),
                "allowedActions": actions,
            },
            sort_at=sub.sent_at,
            row_id=sub.id,
            author_id=review.author_id,
        ))  # fmt: skip
    return rows


def filter_review_rows(
    rows: list[Row],
    user: User,
    *,
    q: str | None = None,
    product_category: str | None = None,
    stage: str | None = None,
    result: str | None = None,
    decision: str | None = None,
    legal_status: str | None = None,
    author: str | None = None,
    action: str | None = None,
) -> list[Row]:
    """검색·필터는 AND. author는 사용자 ID 또는 ME, 생략하면 팀 전체."""
    author_id = user.id if author == "ME" else author
    out = []
    for row in rows:
        d = row.data
        if q and q.lower() not in d["title"].lower():
            continue
        if product_category and d["productCategory"] != product_category:
            continue
        if stage and d["stage"] != stage:
            continue
        if result and d["result"] != result:
            continue
        if decision and d["decision"] != decision:
            continue
        if legal_status and d["legalStatus"] != legal_status:
            continue
        if author_id and row.author_id != author_id:
            continue
        if action and action not in d["allowedActions"]:
            continue
        out.append(row)
    return out


@router.get(
    "/reviews",
    summary="마케팅 검토함(view=ALL, M-41)·법무팀 전송 내역(view=SENT, M-50)",
    description="ALL은 updatedAt 최신순(같으면 reviewId), SENT는 sentAt 최신순(같으면 submissionId). "
    "q는 제품명 포함 검색, author는 사용자 ID 또는 ME, action은 내가 지금 누를 수 있는 버튼. 필터는 AND. "
    "조회 전에 180초가 지난 실행을 RUN_TIMEOUT으로 확정한다",
)
def list_reviews(
    user: Marketer,
    db: DbSession = Depends(get_db),
    view: Literal["ALL", "SENT"] = "ALL",
    q: str | None = None,
    productCategory: ProductCategory | None = None,
    stage: Stage | None = None,
    result: Result | None = None,
    decision: Decision | None = None,
    legalStatus: LegalStatus | None = None,
    author: str | None = None,
    action: Action | None = None,
    cursor: str | None = None,
    limit: Limit = 20,
) -> dict:
    snap = load_snapshot(db)
    rows = review_rows(snap, user) if view == "ALL" else sent_rows(snap, user)
    filters = {
        "q": q, "productCategory": productCategory, "stage": stage, "result": result, "decision": decision,
        "legalStatus": legalStatus, "author": author, "action": action,
    }  # fmt: skip
    rows = filter_review_rows(
        rows, user, q=q, product_category=productCategory, stage=stage, result=result, decision=decision,
        legal_status=legalStatus, author=author, action=action,
    )  # fmt: skip
    # 커서는 조회한 사람·화면에도 묶는다 (author=ME·action은 사람마다 결과가 다름)
    page, next_cursor = memory_page(
        rows, Row.key, limit=limit, cursor=cursor, filters={"view": view, "user": user.id, **filters}
    )
    db.commit()  # 시간 초과 확정 저장
    return {"items": [r.data for r in page], "nextCursor": next_cursor}


# ---------- 법무 행 ----------


def legal_actions(sub: LegalSubmission, user: User) -> list[str]:
    """검토 대기면 법무 누구나 [검토 시작], 검토 중이면 지정된 담당자만 [전송]."""
    if sub.status == PENDING:
        return [START_LEGAL_REVIEW]
    if sub.status == IN_REVIEW and sub.reviewer_id == user.id:
        return [SEND_OPINION]
    return []


def legal_rows(snap: Snapshot, user: User) -> list[Row]:
    reviews = {r.id: r for r in snap.reviews}
    rows = []
    for sub in snap.legal:
        review = reviews.get(sub.review_id)
        report = snap.reports.get(sub.report_run_id)
        rows.append(Row(
            data={
                "submissionId": sub.id,
                "reviewId": sub.review_id,
                "title": review.title if review else None,
                "reportRunId": sub.report_run_id,
                "stage": report.stage if report else None,
                "decision": report.decision if report else None,
                "legalStatus": sub.status,
                "reviewer": user_ref(snap.users.get(sub.reviewer_id)) if sub.reviewer_id else None,
                "sentAt": to_kst(sub.sent_at),
                "decidedAt": to_kst(sub.decided_at),
                "allowedActions": legal_actions(sub, user),
            },
            sort_at=sub.sent_at,
            row_id=sub.id,
        ))  # fmt: skip
    return rows


def kst_day_start(now: datetime, days_ago: int = 0) -> datetime:
    """한국시간 오늘 0시(에서 days_ago일 전). 시간대 포함 값."""
    today = now.astimezone(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=days_ago)


def filter_legal_rows(
    rows: list[Row],
    snap: Snapshot,
    user: User,
    *,
    q: str | None = None,
    status: str | None = None,
    reviewer: str | None = None,
    decided_period: str | None = None,
) -> list[Row]:
    """q는 보고서명(제품명) 포함 검색, reviewer는 담당자 ID 또는 ME, decidedPeriod는 한국시간 기준. 필터는 AND."""
    reviewer_id = user.id if reviewer == "ME" else reviewer
    subs = {s.id: s for s in snap.legal}
    since = None
    if decided_period == "TODAY":
        since = kst_day_start(utcnow())
    elif decided_period == "LAST_7_DAYS":
        since = kst_day_start(utcnow(), 6)  # 오늘 포함 7일
    out = []
    for row in rows:
        sub = subs[row.row_id]
        if q and q.lower() not in (row.data["title"] or "").lower():
            continue
        if status and sub.status != status:
            continue
        if reviewer_id and sub.reviewer_id != reviewer_id:
            continue
        if since and (sub.decided_at is None or sub.decided_at < since):
            continue
        out.append(row)
    return out


@router.get(
    "/legal-submissions",
    summary="법무팀 검토함 (LG-5·LG-6·LG-7 등)",
    description="요청 1건당 1행, sentAt 최신순(같으면 submissionId). status=PENDING·IN_REVIEW·OPINION_SENT, "
    "reviewer는 담당자 ID 또는 ME, decidedPeriod=TODAY·LAST_7_DAYS(한국시간). 목록 조회는 상태를 바꾸지 않는다",
)
def list_legal_submissions(
    user: Lawyer,
    db: DbSession = Depends(get_db),
    q: str | None = None,
    status: SubmissionStatus | None = None,
    reviewer: str | None = None,
    decidedPeriod: Literal["TODAY", "LAST_7_DAYS"] | None = None,
    cursor: str | None = None,
    limit: Limit = 20,
) -> dict:
    snap = load_snapshot(db)
    rows = filter_legal_rows(legal_rows(snap, user), snap, user, q=q, status=status, reviewer=reviewer, decided_period=decidedPeriod)
    filters = {"view": "LEGAL", "user": user.id, "q": q, "status": status, "reviewer": reviewer, "decidedPeriod": decidedPeriod}
    if decidedPeriod:
        filters["day"] = kst_day_start(utcnow()).date().isoformat()  # 날짜가 바뀌면 커서도 바뀜
    page, next_cursor = memory_page(rows, Row.key, limit=limit, cursor=cursor, filters=filters)
    db.commit()
    return {"items": [r.data for r in page], "nextCursor": next_cursor}

