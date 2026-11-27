"""Agent → 백엔드 실행 완료 통지. POST /internal/v1/review-runs/{runId}/completion (설계서 6장 '연동 방향').

처리 순서
1. 서비스 인증 (Authorization: Bearer {AGENT_TOKEN}) → 401
2. 형식 검사 (필수·빈 값·타입) → 422 VALIDATION_ERROR
3. 실행 ID·검토 건 일치 → 없거나 다르면 404
4. 180초가 지났으면 RUN_TIMEOUT으로 먼저 확정
5. 이미 확정된 실행: 같은 runStatus면 200(다시 처리하지 않음), 다르면 409 STATE_CONFLICT
6. 내용 검사 (성공·실패 짝, 전체 판정, 부적합 문장 출처, 위반 유형 코드, schemaVersion) → 422
7. 저장 후 200 (실행 상태 응답과 같은 모양)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.core.deps import get_db, verify_agent_token
from app.core.errors import ApiError
from app.core.security import utcnow
from app.models import Report, Review, ReviewRun
from app.notifications.service import notify
from app.reviews import codes as C
from app.reviews.runs import expire_if_timed_out, fail_run, run_input_text
from app.reviews.schemas import ReportBody, RunCompletion
from app.reviews.state import current_report, run_view

router = APIRouter(dependencies=[Depends(verify_agent_token)])


def _invalid(message: str, field_errors: list[dict]) -> ApiError:
    return ApiError(422, "VALIDATION_ERROR", message, field_errors=field_errors)


def check_shape(run: ReviewRun, body: RunCompletion) -> None:
    """성공이면 report(RA_SUGGEST는 suggestion)만, 실패면 error만."""
    if body.schema_version not in C.SUPPORTED_SCHEMA_VERSIONS:
        raise _invalid("지원하지 않는 schemaVersion입니다.", [{"field": "schemaVersion", "code": "INVALID"}])
    present = {"report": body.report is not None, "suggestion": body.suggestion is not None, "error": body.error is not None}
    if body.run_status == C.SUCCEEDED:
        need = "suggestion" if run.stage == C.RA_SUGGEST else "report"
    else:
        need = "error"
    errors = [] if present[need] else [{"field": need, "code": "REQUIRED"}]
    errors += [{"field": k, "code": "INVALID"} for k, v in present.items() if v and k != need]
    if errors:
        raise _invalid("실행 결과와 맞지 않는 필드가 있습니다. 성공이면 결과, 실패면 error만 보내 주세요.", errors)


def check_report(report: ReportBody) -> None:
    """전체 판정·부적합 문장 출처·위반 유형 코드. 어긴 곳을 한 번에 모두 알려 준다."""
    errors: list[dict] = []
    expected = C.UNSUITABLE if any(f.decision == C.UNSUITABLE for f in report.findings) else C.SUITABLE
    if report.decision != expected:
        errors.append({"field": "report.decision", "code": "INVALID"})
    for i, f in enumerate(report.findings):
        path = f"report.findings[{i}]"
        if f.decision == C.UNSUITABLE:
            if not f.sources:
                errors.append({"field": f"{path}.sources", "code": "REQUIRED"})
            if f.violation_code is None:
                errors.append({"field": f"{path}.violationCode", "code": "REQUIRED"})
            elif f.violation_code not in C.VIOLATION_CODES:
                errors.append({"field": f"{path}.violationCode", "code": "INVALID"})
        elif f.violation_code is not None:
            errors.append({"field": f"{path}.violationCode", "code": "INVALID"})
    if errors:
        raise _invalid("보고서 내용을 확인해 주세요. 판정·출처·위반 유형 규칙에 맞지 않습니다.", errors)


@router.post(
    "/review-runs/{runId}/completion",
    summary="실행 완료 통지 (Agent → 백엔드)",
    description="Authorization: Bearer {AGENT_TOKEN}. 실행 ID·검토 건 일치 확인, 같은 통지는 한 번만 처리. "
    "확정된 실행은 늦게 온 다른 결과로 덮어쓰지 않는다(409). 저장되면 200과 실행 상태",
)
def complete_run(runId: str, body: RunCompletion, db: DbSession = Depends(get_db)):
    run = db.get(ReviewRun, runId, with_for_update=True)
    if run is None or run.review_id != body.review_id:
        raise ApiError(404, "NOT_FOUND", "실행을 찾을 수 없습니다.")

    if expire_if_timed_out(db, run):  # 180초가 지났으면 먼저 RUN_TIMEOUT으로 확정 (늦은 결과는 아래에서 409)
        db.commit()
        run = db.get(ReviewRun, runId, with_for_update=True)

    if run.status in (C.SUCCEEDED, C.FAILED):
        if run.status == body.run_status:
            db.rollback()
            return run_view(run)  # 같은 통지 재전송
        raise ApiError(409, "STATE_CONFLICT", "이미 확정된 실행입니다.")

    check_shape(run, body)
    if body.report is not None:
        check_report(body.report)

    now = utcnow()
    review = db.get(Review, run.review_id)
    run.started_at = run.started_at or now  # 202 처리보다 완료 통지가 먼저 온 경우
    run.updated_at = run.finished_at = now
    review.updated_at = now

    if body.run_status == C.FAILED:
        err = body.error
        fail_run(db, run, err.code, err.message, err.retryable)
    elif run.stage == C.RA_SUGGEST:
        # 보고서 대신 추천 문구만 저장 (판정 없음, 보고서·버전 그대로) → '추천 문구 확인' 팝업
        run.status = C.SUCCEEDED
        run.suggestion = {
            "text": body.suggestion.text,
            "rationale": body.suggestion.rationale,
            "status": C.SUGGESTION_PENDING,
        }
        notify(
            db, review.author_id, "RA_SUGGESTED",
            f"{review.title} · AI 추천 문구가 준비됐습니다. 확인 후 재심의를 진행해 주세요.",
            review_id=review.id, menu="INBOX",
        )  # fmt: skip
    else:
        # 보고서 저장: version = 직전 + 1 (처음 1), reviewedText = 심의한 문구 (AI 심의 원문, 재심의 추천 문구)
        latest = current_report(db, review.id)
        report = body.report
        db.add(
            Report(
                run_id=run.id,
                review_id=review.id,
                stage=run.stage,
                version=(latest.version + 1) if latest else 1,
                reviewed_text=run_input_text(db, run, review),
                decision=report.decision,
                summary=report.summary,
                improvement_note=report.improvement_note,
                findings=[f.model_dump(by_alias=True) for f in report.findings],
                created_at=now,
            )
        )
        run.status = C.SUCCEEDED
        if run.stage == C.RA_RECHECK:
            notify(
                db, review.author_id, "RA_COMPLETED",
                f"{review.title} · 재심의 결과 {C.DECISION_LABEL[report.decision]}입니다.",
                review_id=review.id, menu="INBOX",
            )  # fmt: skip

    db.commit()
    return run_view(run)
