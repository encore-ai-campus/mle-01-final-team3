"""검토 요청·실행 상태·결과 보고서 조회 API. 설계서 3장·6장·7장.

POST /reviews                                   신규 [검토] → AI 심의 실행 (202)
GET  /reviews/{reviewId}                        AI 검토 보고서
POST /reviews/{reviewId}/ra-runs                [AI 추천 요청] → 추천 문구 생성 실행 (202)
POST /reviews/{reviewId}/ra-runs/{runId}/recheck  '추천 문구 확인' [재심의] → 재심의 실행 (202)
POST /reviews/{reviewId}/ra-runs/{runId}/dismiss  '추천 문구 확인' [닫기] (200)
GET  /review-runs/{runId}                       실행 상태 (폴링)
POST /review-runs/{runId}/retry                 실패한 실행 [다시 검토] (202)

실행을 만드는 API는 202와 Location: /api/v1/review-runs/{runId}를 주고, Idempotency-Key를 받는다.
"""

import json

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session as DbSession

from app.core.activity import log_activity
from app.core.deps import Marketer, Staff, get_db, lock_actor
from app.core.errors import ApiError
from app.core.idempotency import IdemKey, run_idempotent
from app.core.ids import new_id
from app.core.security import utcnow
from app.models import Review, ReviewAttachment, ReviewRun
from app.reviews import codes as C
from app.reviews.attachments import check_review_attachments
from app.reviews.runs import create_run, expire_if_timed_out
from app.reviews.schemas import ReviewCreate
from app.reviews.state import (
    accepted_view,
    detail_view,
    get_review_or_404,
    load_state,
    pending_suggestion,
    require_action,
    require_author,
    run_view,
)

router = APIRouter()

API_PREFIX = "/api/v1"
_ACCEPTED = {202: {"description": "접수. Location: /api/v1/review-runs/{runId}"}}


def with_location(resp: Response) -> Response:
    """202 응답에 실행 조회 주소를 붙인다. 같은 Idempotency-Key로 다시 받은 응답에도 붙인다."""
    if resp.status_code == 202:
        run_id = json.loads(resp.body)["runId"]
        resp.headers["Location"] = f"{API_PREFIX}/review-runs/{run_id}"
    return resp


def get_run_or_404(db: DbSession, run_id: str) -> ReviewRun:
    run = db.get(ReviewRun, run_id)
    if run is None:
        raise ApiError(404, "NOT_FOUND", "실행을 찾을 수 없습니다.")
    return run


# ---------- 검토 요청 ----------


@router.post(
    "/reviews",
    status_code=202,
    responses=_ACCEPTED,
    summary="신규 [검토] (M-8)",
    description="새 검토 건과 AI 심의 실행(AI_SCREENING)을 만든다. 빈칸 422(M-9). "
    "attachmentIds는 본인이 올린, 아직 다른 검토 건에 붙지 않은 파일만(아니면 422), 합계 10MB 초과 413",
)
def create_review(
    body: ReviewCreate,
    user: Marketer,
    background: BackgroundTasks,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")  # 지금도 ACTIVE 마케팅 담당자인지 (users 행 공유 잠금)
        attachment_ids = check_review_attachments(db, user, body.attachment_ids)
        now = utcnow()
        review = Review(
            id=new_id(db, "revw"),
            author_id=user.id,
            title=body.title,
            product_category=body.product_category,
            channel=body.channel,
            main_ingredients=body.main_ingredients,
            text=body.text,
            created_at=now,
            updated_at=now,
        )
        db.add(review)
        db.flush()
        for aid in attachment_ids:
            db.add(ReviewAttachment(review_id=review.id, attachment_id=aid))
        run = create_run(db, review, C.AI_SCREENING, background)
        log_activity(db, user.id, "REVIEW_REQUESTED", review.title)
        db.flush()
        return 202, accepted_view(run)

    return with_location(run_idempotent(db, user.id, idempotency_key, body.model_dump(mode="json"), work))


# ---------- 보고서 ----------


@router.get(
    "/reviews/{reviewId}",
    summary="AI 검토 보고서 (M-15·M-24·M-30·M-37 등)",
    description="원문, 최신 성공 보고서(version·reviewedText), 직전 버전 previousReport(v1이면 null), "
    "확인 대기 추천 문구 suggestion, 실행·법무 상태, allowedActions. "
    "다른 작성자의 보고서는 allowedActions=[]. 조회할 때마다 활동 로그 REPORT_VIEWED",
)
def get_review(reviewId: str, user: Marketer, db: DbSession = Depends(get_db)):
    review = get_review_or_404(db, reviewId)
    state = load_state(db, review)
    if expire_if_timed_out(db, state.run):
        state = load_state(db, review)
    log_activity(db, user.id, "REPORT_VIEWED", f"{review.title} 검토 보고서")
    result = detail_view(db, state, user)
    db.commit()
    return result


# ---------- AI 추천 요청 · 재심의 · 닫기 ----------


@router.post(
    "/reviews/{reviewId}/ra-runs",
    status_code=202,
    responses=_ACCEPTED,
    summary="[AI 추천 요청] (M-24 → M-25)",
    description="부적합 보고서 또는 검토 의견을 받은 보고서에서. 추천 문구만 만든다(stage=RA_SUGGEST, 판정 없음). "
    "횟수 제한 없음. 허용되지 않는 상태면 409 STATE_CONFLICT",
)
def request_suggestion(
    reviewId: str,
    user: Marketer,
    background: BackgroundTasks,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")  # 지금도 ACTIVE 마케팅 담당자인지 (users 행 공유 잠금)
        # 검토 건 행 잠금: 동시에 두 번 요청해도 뒤 요청은 앞 요청이 끝난 뒤 상태를 보고 409가 된다 (실행 중인 건은 하나)
        review = get_review_or_404(db, reviewId, lock=True)
        state = load_state(db, review)
        expire_if_timed_out(db, state.run)
        require_action(state, user, C.RUN_RA)
        run = create_run(db, review, C.RA_SUGGEST, background)
        log_activity(db, user.id, "RA_RECHECK_REQUESTED", review.title)
        db.flush()
        return 202, accepted_view(run)

    return with_location(run_idempotent(db, user.id, idempotency_key, {"reviewId": reviewId}, work))


def _pending_suggestion_run(db: DbSession, reviewId: str, runId: str, user, action: str):
    review = get_review_or_404(db, reviewId, lock=True)  # 검토 건 → 실행 순서로 잠근다
    run = db.get(ReviewRun, runId, with_for_update=True)
    if run is None or run.review_id != reviewId or run.stage != C.RA_SUGGEST or not run.suggestion:
        raise ApiError(404, "NOT_FOUND", "추천 문구를 찾을 수 없습니다.")
    state = load_state(db, review)
    require_author(state, user)
    if pending_suggestion(run) is None:
        raise ApiError(409, "STATE_CONFLICT", "이미 처리한 추천 문구입니다. 최신 상태를 다시 조회해 주세요.")
    require_action(state, user, action)
    return review, run


@router.post(
    "/reviews/{reviewId}/ra-runs/{runId}/recheck",
    status_code=202,
    responses=_ACCEPTED,
    summary="'추천 문구 확인' [재심의]",
    description="runId는 suggestion.runId. 추천 문구를 AI 심의와 같은 흐름으로 재심의(stage=RA_RECHECK). "
    "성공하면 보고서 버전 +1. 작성자만, 확인 대기일 때만. 이미 [재심의]·[닫기]한 문구는 409",
)
def recheck_suggestion(
    reviewId: str,
    runId: str,
    user: Marketer,
    background: BackgroundTasks,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")  # 지금도 ACTIVE 마케팅 담당자인지 (users 행 공유 잠금)
        review, sug_run = _pending_suggestion_run(db, reviewId, runId, user, C.RECHECK_SUGGESTION)
        sug_run.suggestion = {**sug_run.suggestion, "status": C.SUGGESTION_RECHECKED}
        sug_run.updated_at = utcnow()
        run = create_run(db, review, C.RA_RECHECK, background, input_text=sug_run.suggestion["text"])
        log_activity(db, user.id, "SUGGESTION_RECHECKED", review.title)
        db.flush()
        return 202, accepted_view(run)

    return with_location(
        run_idempotent(db, user.id, idempotency_key, {"reviewId": reviewId, "runId": runId}, work)
    )


@router.post(
    "/reviews/{reviewId}/ra-runs/{runId}/dismiss",
    summary="'추천 문구 확인' [닫기]",
    description="추천 문구를 버린다. 보고서는 직전 그대로, 버튼은 AI 추천 요청 전으로. 이미 처리한 문구는 409. "
    "응답은 GET /reviews/{reviewId}와 같은 모양",
)
def dismiss_suggestion(reviewId: str, runId: str, user: Marketer, db: DbSession = Depends(get_db)):
    review, sug_run = _pending_suggestion_run(db, reviewId, runId, user, C.DISMISS_SUGGESTION)
    now = utcnow()
    sug_run.suggestion = {**sug_run.suggestion, "status": C.SUGGESTION_DISMISSED}
    sug_run.updated_at = review.updated_at = now
    log_activity(db, user.id, "SUGGESTION_DISMISSED", review.title)
    db.flush()
    result = detail_view(db, load_state(db, review), user)
    db.commit()
    return result


# ---------- 실행 상태 ----------


@router.get(
    "/review-runs/{runId}",
    summary="실행 상태 조회 (폴링)",
    description="QUEUED·RUNNING이면 2초 → 4초 → 5초 간격으로 다시 조회. 실행을 만든 뒤 180초가 지나면 FAILED / RUN_TIMEOUT",
)
def get_run(runId: str, user: Staff, db: DbSession = Depends(get_db)):
    run = get_run_or_404(db, runId)
    expire_if_timed_out(db, run)
    result = run_view(run)
    db.commit()
    return result


@router.post(
    "/review-runs/{runId}/retry",
    status_code=202,
    responses=_ACCEPTED,
    summary="실행 재시도 ([다시 검토] M-11·M-26)",
    description="최신 실패 실행만, 최초 실행별 최대 2회(한도 도달 409 RETRY_LIMIT_REACHED). "
    "실행 중·재시도 불가(error.retryable=false)면 409 STATE_CONFLICT. 재심의 재시도는 같은 추천 문구로 다시 심의",
)
def retry_run(
    runId: str,
    user: Marketer,
    background: BackgroundTasks,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work():
        lock_actor(db, user, "MARKETING")  # 지금도 ACTIVE 마케팅 담당자인지 (users 행 공유 잠금)
        run = get_run_or_404(db, runId)
        # 검토 건 행 잠금: 같은 실패 실행을 동시에 두 번 재시도해도 새 실행은 하나만 생긴다 (뒤 요청은 409)
        review = get_review_or_404(db, run.review_id, lock=True)
        state = load_state(db, review)
        expire_if_timed_out(db, state.run)
        require_author(state, user)
        if state.run is None or state.run.id != run.id or run.status != C.FAILED:
            raise ApiError(409, "STATE_CONFLICT", "최신 실패 실행만 다시 시도할 수 있습니다.")
        if not run.error_retryable:
            raise ApiError(
                409, "STATE_CONFLICT",
                "다시 시도해도 같은 결과가 나오는 오류입니다. 심의를 취소하고 문구나 파일을 고쳐 새로 검토 요청해 주세요.",
            )  # fmt: skip
        if (run.attempt or 1) >= C.MAX_ATTEMPT:
            raise ApiError(409, "RETRY_LIMIT_REACHED", "다시 시도할 수 있는 횟수를 모두 사용했습니다.")
        new_run = create_run(db, review, run.stage, background, retry_of=run)
        log_activity(db, user.id, "RUN_RETRIED", review.title)
        db.flush()
        return 202, accepted_view(new_run)

    return with_location(run_idempotent(db, user.id, idempotency_key, {"runId": runId}, work))
