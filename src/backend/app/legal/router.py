"""법무 담당자 API. 설계서 3장 '업무 상태'·5장 '법무팀 검토함'·6장.

GET  /legal-submissions/{submissionId}          검토 보고서 (LG-12·LG-20·LG-21). 상태를 바꾸지 않는다
POST /legal-submissions/{submissionId}/start    [검토 시작] → 담당자 지정 (PENDING → IN_REVIEW)
POST /legal-submissions/{submissionId}/opinion  검토 의견 [전송] (IN_REVIEW → OPINION_SENT)

법무 상태: 검토 대기(PENDING) → 검토 중(IN_REVIEW) → 검토 의견 전송(OPINION_SENT).
먼저 [검토 시작]을 누른 사람만 담당자가 되고, 담당자만 의견을 보낸다. 다른 법무 담당자는 읽기만 한다.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.core.activity import log_activity
from app.core.deps import Lawyer, get_db, lock_actor
from app.core.errors import ApiError
from app.core.idempotency import IdemKey, run_idempotent
from app.core.schemas import CamelModel, Text
from app.core.security import utcnow
from app.core.times import to_kst
from app.models import LegalSubmission, Report, Review, User
from app.notifications.service import notify
from app.reviews import codes as C
from app.reviews.state import report_view, user_ref

router = APIRouter(prefix="/legal-submissions")


class OpinionRequest(CamelModel):
    reason: Text  # 검토 의견 (필수). 적합·부적합 값은 보내지 않는다


def get_submission_or_404(db: DbSession, submission_id: str, *, lock: bool = False) -> LegalSubmission:
    sub = db.get(LegalSubmission, submission_id, with_for_update=lock or None, populate_existing=lock)
    if sub is None:
        raise ApiError(404, "NOT_FOUND", "보고서를 찾을 수 없습니다.")
    return sub


def detail_actions(sub: LegalSubmission, user: User) -> list[str]:
    """상세 화면 버튼. 배정된 담당자이고 검토 중이면 [전송]만. 그 외(다른 담당자·검토 대기·전송 완료)는 빈 배열."""
    if sub.status == C.IN_REVIEW and sub.reviewer_id == user.id:
        return [C.SEND_OPINION]
    return []


def assignment_view(db: DbSession, sub: LegalSubmission, user: User) -> dict:
    """[검토 시작] 응답: 현재 법무 상태·담당자·지정 시각·버튼."""
    return {
        "submissionId": sub.id,
        "legalStatus": sub.status,
        "reviewer": user_ref(db.get(User, sub.reviewer_id)) if sub.reviewer_id else None,
        "startedAt": to_kst(sub.started_at),
        "allowedActions": detail_actions(sub, user),
    }


def submission_detail(db: DbSession, sub: LegalSubmission, user: User) -> dict:
    """GET /legal-submissions/{submissionId} 응답 (설계서 6장 '법무 검토 보고서 응답'). 보고서는 요청 시점에 고정된 것."""
    review = db.get(Review, sub.review_id)
    report = db.get(Report, sub.report_run_id)
    return {
        "submissionId": sub.id,
        "reviewId": review.id,
        "title": review.title,
        "productCategory": review.product_category,
        "channel": review.channel,
        "mainIngredients": review.main_ingredients or [],
        "text": report.reviewed_text,  # 요청 시점의 광고 문구 (재심의 보고서면 AI 추천 문구)
        "sender": user_ref(db.get(User, sub.sender_id)) if sub.sender_id else None,
        "sentAt": to_kst(sub.sent_at),
        "reportRunId": sub.report_run_id,
        "stage": report.stage,
        "decision": report.decision,
        "report": report_view(report),
        "legalStatus": sub.status,
        "reviewer": user_ref(db.get(User, sub.reviewer_id)) if sub.reviewer_id else None,
        "startedAt": to_kst(sub.started_at),
        "decidedAt": to_kst(sub.decided_at),
        "reason": sub.reason,
        "allowedActions": detail_actions(sub, user),
    }


@router.get(
    "/{submissionId}",
    summary="법무 검토 보고서 (LG-12·LG-20·LG-21)",
    description="법무 담당자만. 요청 시점에 고정된 보고서와 법무 상태·검토 의견. 상태를 바꾸지 않는다. "
    "조회할 때마다 활동 로그 REPORT_VIEWED. 배정된 담당자이고 검토 중이면 allowedActions=[SEND_OPINION]",
)
def get_submission(submissionId: str, user: Lawyer, db: DbSession = Depends(get_db)):
    sub = get_submission_or_404(db, submissionId)
    result = submission_detail(db, sub, user)
    log_activity(db, user.id, "REPORT_VIEWED", f"{result['title']} 검토 보고서")
    db.commit()
    return result


@router.post(
    "/{submissionId}/start",
    summary="[검토 시작] → 담당자 지정 (PENDING → IN_REVIEW)",
    description="검토 대기 건이면 누른 사람을 담당자로 지정한다. 여러 명이 동시에 눌러도 첫 지정만 기록한다. "
    "이미 지정됐거나 의견을 보낸 건이면 바꾸지 않고 200과 현재 상태를 준다(다른 담당자면 allowedActions=[]로 읽기 전용)",
)
def start_review(submissionId: str, user: Lawyer, db: DbSession = Depends(get_db)):
    lock_actor(db, user, "LEGAL")
    sub = get_submission_or_404(db, submissionId, lock=True)  # 동시에 눌러도 한 명만 지정되도록 잠근다
    if sub.status == C.PENDING:
        now = utcnow()
        sub.status, sub.reviewer_id, sub.started_at = C.IN_REVIEW, user.id, now
        review = db.get(Review, sub.review_id)
        review.updated_at = now
    result = assignment_view(db, sub, user)
    db.commit()
    return result


@router.post(
    "/{submissionId}/opinion",
    summary="검토 의견 [전송] (LG-13·LG-18)",
    description="reason(검토 의견) 필수, 비어 있으면 422. 지정된 담당자만(아니면 403), 검토 중일 때만(아니면 409 STATE_CONFLICT). "
    "성공하면 legalStatus=OPINION_SENT, decidedAt을 주고 요청한 마케팅 담당자에게 알린다",
)
def send_opinion(
    submissionId: str,
    body: OpinionRequest,
    user: Lawyer,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "LEGAL")
        sub = get_submission_or_404(db, submissionId, lock=True)
        if sub.status != C.IN_REVIEW:
            raise ApiError(409, "STATE_CONFLICT", "검토 중인 건에만 의견을 보낼 수 있습니다. 최신 상태를 다시 조회해 주세요.")
        if sub.reviewer_id != user.id:
            raise ApiError(403, "FORBIDDEN", "담당자로 지정된 사람만 검토 의견을 보낼 수 있습니다.")
        now = utcnow()
        sub.status, sub.reason, sub.decided_at = C.OPINION_SENT, body.reason, now
        review = db.get(Review, sub.review_id)
        review.updated_at = now
        # 담당 건 이관 때 sender_id도 받는 사람으로 바뀌므로, 지금 담당하는 마케팅 담당자에게 간다
        if sub.sender_id:
            notify(
                db, sub.sender_id, "LEGAL_OPINION_SENT", f"{review.title} · 법무팀 검토 의견이 도착했습니다.",
                review_id=review.id, submission_id=sub.id, menu="SENT_LIST",
            )  # fmt: skip
        log_activity(db, user.id, "LEGAL_OPINION_SENT", review.title)
        return 200, {
            "submissionId": sub.id,
            "legalStatus": sub.status,
            "reviewer": user_ref(user),
            "decidedAt": to_kst(sub.decided_at),
            "reason": sub.reason,
            "allowedActions": detail_actions(sub, user),
        }

    payload = {"submissionId": submissionId, **body.model_dump(by_alias=True)}
    return run_idempotent(db, user.id, idempotency_key, payload, work)
