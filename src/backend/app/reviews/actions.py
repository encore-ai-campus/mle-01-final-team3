"""마케팅 보고서 화면의 결정 버튼. 설계서 3장 '업무 상태'·6장.

POST /reviews/{reviewId}/legal-submissions   [법무 검토 요청] → [요청] (201)
POST /reviews/{reviewId}/close               [요청 안 함]·[게시 및 완료]·[심의 취소] (200)

둘 다 작성자만, Idempotency-Key를 받는다. 버튼을 누를 수 있는지는 상세 화면과 같은 allowedActions 규칙(state.py)으로 판단한다.
"""

from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.activity import log_activity
from app.core.deps import Marketer, get_db, lock_actor
from app.core.errors import ApiError
from app.core.idempotency import IdemKey, run_idempotent
from app.core.ids import new_id
from app.core.schemas import CamelModel, Text
from app.core.security import utcnow
from app.core.times import to_kst
from app.models import LegalSubmission, Report, User
from app.notifications.service import notify
from app.reviews import codes as C
from app.reviews.runs import expire_if_timed_out
from app.reviews.state import get_review_or_404, load_state, require_action

router = APIRouter()


class LegalRequest(CamelModel):
    report_run_id: Text  # 요청할 적합 보고서의 실행 ID (상세 응답의 report.runId)


class CloseRequest(CamelModel):
    close_type: Literal["ENDED", "PUBLISHED", "CANCELED"]


@router.post(
    "/reviews/{reviewId}/legal-submissions",
    status_code=201,
    summary="[법무 검토 요청] (M-17·M-31·M-33·M-40·M-59 확인창 → [요청])",
    description="최신 성공 보고서가 적합일 때 그 보고서의 reportRunId를 보낸다. 법무팀 검토함에 넣고 법무팀 전체에 알린다. "
    "요청한 문구·판정·보고서는 요청 시점으로 고정. 같은 보고서로 이미 요청했거나 최신 보고서가 아니면 409 STATE_CONFLICT",
)
def request_legal_review(
    reviewId: str,
    body: LegalRequest,
    user: Marketer,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")
        review = get_review_or_404(db, reviewId, lock=True)
        state = load_state(db, review)
        if expire_if_timed_out(db, state.run):
            state = load_state(db, review)
        report = db.get(Report, body.report_run_id)
        if report is None or report.review_id != review.id:
            raise ApiError(
                422, "VALIDATION_ERROR", "요청할 보고서를 찾을 수 없습니다.",
                field_errors=[{"field": "reportRunId", "code": "INVALID"}],
            )  # fmt: skip
        require_action(state, user, C.SEND_TO_LEGAL)  # 작성자·끝나지 않음·최신 보고서 적합·아직 요청 안 함
        if state.report is None or state.report.run_id != report.run_id:
            raise ApiError(409, "STATE_CONFLICT", "최신 보고서로만 검토를 요청할 수 있습니다. 최신 상태를 다시 조회해 주세요.")

        now = utcnow()
        sub = LegalSubmission(
            id=new_id(db, "sub"),
            review_id=review.id,
            report_run_id=report.run_id,
            sender_id=user.id,
            status=C.PENDING,
            sent_at=now,
        )
        db.add(sub)
        try:
            db.flush()  # 같은 보고서 중복 요청은 report_run_id UNIQUE가 막는다
        except IntegrityError:
            raise ApiError(409, "STATE_CONFLICT", "이미 검토를 요청한 보고서입니다.") from None
        review.updated_at = now

        legal_team = db.scalars(select(User.id).where(User.role == "LEGAL", User.status == "ACTIVE")).all()
        for legal_id in legal_team:
            notify(
                db, legal_id, "SUBMISSION_RECEIVED", f"{review.title} · 새 검토 요청이 접수되었습니다.",
                review_id=review.id, submission_id=sub.id, menu="INBOX",
            )  # fmt: skip
        log_activity(db, user.id, "LEGAL_SENT", review.title)
        return 201, {
            "submissionId": sub.id,
            "reviewId": review.id,
            "reportRunId": sub.report_run_id,
            "legalStatus": sub.status,
            "sentAt": to_kst(sub.sent_at),
        }

    payload = {"reviewId": reviewId, **body.model_dump(by_alias=True)}
    return run_idempotent(db, user.id, idempotency_key, payload, work)


@router.post(
    "/reviews/{reviewId}/close",
    summary="끝 처리: [요청 안 함](ENDED)·[게시 및 완료](PUBLISHED)·[심의 취소](CANCELED)",
    description="ENDED: 적합이고 법무 검토를 요청하지 않은 건. PUBLISHED: 검토 의견을 받고 게시 가능으로 정한 건. "
    "CANCELED: 부적합, 검토 의견 후 수정 필요, 또는 재시도할 수 없는 오류로 첫 심의가 실패한 건. "
    "허용되지 않는 상태 409 STATE_CONFLICT, 이미 끝난 건 409 REVIEW_CLOSED. 이후 모든 버튼이 사라진다",
)
def close_review(
    reviewId: str,
    body: CloseRequest,
    user: Marketer,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")
        review = get_review_or_404(db, reviewId, lock=True)
        state = load_state(db, review)
        if expire_if_timed_out(db, state.run):
            state = load_state(db, review)
        require_action(state, user, C.CLOSE_ACTION[body.close_type])
        now = utcnow()
        review.closed_type, review.closed_at, review.updated_at = body.close_type, now, now
        log_activity(db, user.id, "REVIEW_CLOSED", review.title)
        return 200, {"reviewId": review.id, "closeType": review.closed_type, "closedAt": to_kst(review.closed_at)}

    payload = {"reviewId": reviewId, **body.model_dump(by_alias=True)}
    return run_idempotent(db, user.id, idempotency_key, payload, work)
