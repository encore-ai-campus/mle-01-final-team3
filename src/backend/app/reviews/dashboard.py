"""양 팀 대시보드. 설계서 5장 '양 팀 대시보드와 할 일' (M-1·LG-1).

GET /dashboard?recentLimit=5 → {role, asOf, summary, tasks, recentReports}

- 할 일 카드 건수는 연결된 검토함 목록과 같은 함수·같은 조건으로 센다(lists.py). 그래서 카드 숫자와 목록 건수가 같다.
- 최근 결과(recentReports)는 각 검토함의 기본 정렬·행 형식 그대로 앞에서 recentLimit건.
- 윗칸(summary)은 마케팅·법무 모두 팀 전체의 이번 달(한국시간 1일 0시부터) 건수. 할 일 카드는 개인 기준.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DbSession

from app.core.deps import Staff, get_db
from app.core.security import utcnow
from app.core.times import to_kst
from app.models import User
from app.reviews import codes as C
from app.reviews.lists import (
    Row,
    Snapshot,
    filter_legal_rows,
    filter_review_rows,
    kst_day_start,
    legal_rows,
    load_snapshot,
    review_rows,
)

router = APIRouter()


def _recent(rows: list[Row], limit: int) -> list[dict]:
    return [r.data for r in sorted(rows, key=Row.key, reverse=True)[:limit]]


def month_start():
    """한국시간 이번 달 1일 0시."""
    return kst_day_start(utcnow()).replace(day=1)


def marketing_dashboard(snap: Snapshot, user: User, limit: int) -> dict:
    rows = review_rows(snap, user)
    count = lambda **f: len(filter_review_rows(rows, user, author="ME", **f))  # noqa: E731
    since = month_start()
    return {
        "summary": {
            # 팀 전체 검토 건 단위, 이번 달(한국시간). 화면: 이번 달 심의 · 이번 달 AI 추천 · 이번 달 검토 요청
            "completedReviews": len({r.review_id for r in snap.reports.values() if r.created_at >= since}),  # 보고서가 나온 건
            "raReviews": len({r.review_id for r in snap.ra_runs if r.created_at >= since}),  # AI 추천을 요청한 건
            "legalSentReviews": len({s.review_id for s in snap.legal if s.sent_at >= since}),  # 법무 검토를 요청한 건
        },
        "tasks": {
            "sendToLegal": count(decision=C.SUITABLE, legal_status="NOT_SENT", action=C.SEND_TO_LEGAL),  # M-5
            "unsuitableToAct": count(decision=C.UNSUITABLE, action=C.RUN_RA),  # M-6
            "opinionToCheck": count(legal_status=C.OPINION_SENT, action=C.PUBLISH),  # M-7
            "suggestionToCheck": count(action=C.RECHECK_SUGGESTION),
        },
        "recentReports": _recent(rows, limit),
    }


def legal_dashboard(snap: Snapshot, user: User, limit: int) -> dict:
    rows = legal_rows(snap, user)
    count = lambda **f: len(filter_legal_rows(rows, snap, user, **f))  # noqa: E731
    since = month_start()
    return {
        "summary": {
            # 요청 건 단위, 이번 달(한국시간)
            "receivedThisMonth": sum(1 for s in snap.legal if s.sent_at >= since),
            "opinionSentThisMonth": sum(1 for s in snap.legal if s.decided_at and s.decided_at >= since),
        },
        "tasks": {
            "pending": count(status="PENDING"),  # LG-5
            "inReview": count(status="IN_REVIEW", reviewer="ME"),  # LG-6
            "completedToday": count(decided_period="TODAY"),  # LG-7, 법무팀 전체
        },
        "recentReports": _recent(rows, limit),
    }


@router.get(
    "/dashboard",
    summary="대시보드 (마케팅 M-1·법무 LG-1)",
    description="세션 역할에 맞는 {role, asOf, summary, tasks, recentReports}. recentLimit 기본 5, 최대 20. "
    "할 일 카드 건수는 연결된 검토함 목록과 같은 조건으로 센다",
)
def dashboard(
    user: Staff,
    db: DbSession = Depends(get_db),
    recentLimit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> dict:
    snap = load_snapshot(db)
    body = marketing_dashboard(snap, user, recentLimit) if user.role == "MARKETING" else legal_dashboard(snap, user, recentLimit)
    db.commit()  # 시간 초과 확정 저장
    return {"role": user.role, "asOf": to_kst(utcnow()), **body}
