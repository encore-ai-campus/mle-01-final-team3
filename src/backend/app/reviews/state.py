"""검토 건의 현재 상태와 버튼(allowedActions) 계산, 응답 모양 만들기.

검토 건 상태는 따로 저장하지 않고 DB 행에서 계산한다.
- 최근 실행: review_runs 중 가장 최근에 만든 것 (실패 포함) → runStatus, latestRunId
- 최신 보고서: reports 중 version이 가장 큰 것 → report, previousReport(version - 1)
- 확인 대기 추천 문구: 최근 실행이 성공한 RA_SUGGEST이고 suggestion.status=PENDING
- 법무: legal_submissions 중 가장 최근 요청

버튼 규칙 (설계서 3장·7장):
| 상태 | 버튼 |
| 끝남(closed) · 실행 중 · 작성자가 아님 | [] |
| 실패, 재시도 가능 | RETRY_RUN (+ 보고서가 있으면 CANCEL) |
| 실패, 재시도 불가 | CANCEL |
| 확인 대기 추천 문구 | RECHECK_SUGGESTION, DISMISS_SUGGESTION |
| 최신 보고서로 법무 요청 후 검토 대기·검토 중 | [] |
| 최신 보고서로 검토 의견 받음 | PUBLISH, RUN_RA, CANCEL |
| 적합 | SEND_TO_LEGAL, END |
| 부적합 | RUN_RA, CANCEL |
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.core.times import to_kst
from app.models import LegalSubmission, Report, Review, ReviewRun, User
from app.reviews import codes as C

# ---------- 조회 ----------


def latest_run(db: DbSession, review_id: str) -> ReviewRun | None:
    return db.scalars(
        select(ReviewRun)
        .where(ReviewRun.review_id == review_id)
        .order_by(ReviewRun.created_at.desc())
        .limit(1)
    ).first()


def current_report(db: DbSession, review_id: str) -> Report | None:
    return db.scalars(
        select(Report).where(Report.review_id == review_id).order_by(Report.version.desc()).limit(1)
    ).first()


def report_of_version(db: DbSession, review_id: str, version: int) -> Report | None:
    return db.scalars(select(Report).where(Report.review_id == review_id, Report.version == version)).first()


def latest_legal(db: DbSession, review_id: str) -> LegalSubmission | None:
    return db.scalars(
        select(LegalSubmission)
        .where(LegalSubmission.review_id == review_id)
        .order_by(LegalSubmission.sent_at.desc())
        .limit(1)
    ).first()


def pending_suggestion(run: ReviewRun | None) -> dict | None:
    if (
        run is not None
        and run.stage == C.RA_SUGGEST
        and run.status == C.SUCCEEDED
        and run.suggestion
        and run.suggestion.get("status") == C.SUGGESTION_PENDING
    ):
        return run.suggestion
    return None


@dataclass
class ReviewState:
    review: Review
    author: User | None
    run: ReviewRun | None
    report: Report | None
    legal: LegalSubmission | None

    @property
    def actions(self) -> list[str]:
        """작성자 기준 버튼. 다른 사람에게는 actions_for()가 빈 배열을 준다."""
        return base_actions(self.review, self.run, self.report, self.legal)

    def actions_for(self, user: User) -> list[str]:
        return self.actions if self.review.author_id == user.id else []


def load_state(db: DbSession, review: Review) -> ReviewState:
    return ReviewState(
        review=review,
        author=db.get(User, review.author_id) if review.author_id else None,
        run=latest_run(db, review.id),
        report=current_report(db, review.id),
        legal=latest_legal(db, review.id),
    )


def get_review_or_404(db: DbSession, review_id: str) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise ApiError(404, "NOT_FOUND", "보고서를 찾을 수 없습니다.")
    return review


# ---------- 버튼 ----------


def base_actions(review: Review, run: ReviewRun | None, report: Report | None, legal: LegalSubmission | None) -> list[str]:
    if review.closed_type or run is None or run.status in C.ACTIVE:
        return []
    if run.status == C.FAILED:
        if not run.error_retryable:  # 입력 문제: 다시 해도 같은 결과 → 심의 취소만
            return [C.CANCEL]
        return [C.RETRY_RUN, C.CANCEL] if report else [C.RETRY_RUN]
    if pending_suggestion(run):
        return [C.RECHECK_SUGGESTION, C.DISMISS_SUGGESTION]
    if report is None:
        return []
    if legal is not None and legal.report_run_id == report.run_id:
        return [C.PUBLISH, C.RUN_RA, C.CANCEL] if legal.status == C.OPINION_SENT else []
    if report.decision == C.UNSUITABLE:
        return [C.RUN_RA, C.CANCEL]
    return [C.SEND_TO_LEGAL, C.END]


def require_author(state: ReviewState, user: User) -> None:
    if state.review.author_id != user.id:
        raise ApiError(403, "FORBIDDEN", "작성자만 사용할 수 있습니다.")
    if state.review.closed_type:
        raise ApiError(409, "REVIEW_CLOSED", "이미 끝난 검토 건입니다.")


def require_action(state: ReviewState, user: User, action: str) -> None:
    require_author(state, user)
    if action not in state.actions:
        raise ApiError(409, "STATE_CONFLICT", "현재 상태에서는 할 수 없는 작업입니다. 최신 상태를 다시 조회해 주세요.")


# ---------- 응답 모양 ----------


def user_ref(user: User | None) -> dict | None:
    return {"userId": user.id, "name": user.name} if user else None


def accepted_view(run: ReviewRun) -> dict:
    """202 접수 응답 (설계서 7장)."""
    return {"reviewId": run.review_id, "runId": run.id, "stage": run.stage, "runStatus": run.status}


def run_view(run: ReviewRun) -> dict:
    """GET /review-runs/{runId} 응답."""
    error = None
    if run.error_code:
        error = {"code": run.error_code, "message": run.error_message, "retryable": bool(run.error_retryable)}
    return {
        **accepted_view(run),
        "attempt": run.attempt,
        "updatedAt": to_kst(run.updated_at),
        "startedAt": to_kst(run.started_at),
        "finishedAt": to_kst(run.finished_at),
        "error": error,
    }


def report_view(report: Report) -> dict:
    return {
        "runId": report.run_id,
        "stage": report.stage,
        "version": report.version,
        "reviewedText": report.reviewed_text,
        "decision": report.decision,
        "summary": report.summary,
        "improvementNote": report.improvement_note,
        "findings": report.findings,
    }


def detail_view(db: DbSession, state: ReviewState, user: User) -> dict:
    """GET /reviews/{reviewId} 응답 (설계서 6장 '결과 보고서 조회 API 상세')."""
    review, report, run, legal = state.review, state.report, state.run, state.legal

    previous = None
    if report is not None and report.version > 1:
        prev = report_of_version(db, review.id, report.version - 1)
        if prev is not None:
            previous = {"version": prev.version, "decision": prev.decision, "reviewedText": prev.reviewed_text}

    suggestion = None
    if (sug := pending_suggestion(run)) is not None:
        suggestion = {
            "runId": run.id,
            "text": sug["text"],
            "rationale": sug["rationale"],
            "createdAt": to_kst(run.finished_at),
        }

    legal_view = None
    if legal is not None:
        legal_view = {
            "submissionId": legal.id,
            "legalStatus": legal.status,
            "reviewer": user_ref(db.get(User, legal.reviewer_id)) if legal.reviewer_id else None,
            "sentAt": to_kst(legal.sent_at),
            "decidedAt": to_kst(legal.decided_at),
            "reason": legal.reason,
        }

    return {
        "reviewId": review.id,
        "title": review.title,
        "productCategory": review.product_category,
        "text": review.text,
        "author": user_ref(state.author),
        "createdAt": to_kst(review.created_at),
        "runStatus": run.status if run else None,
        "latestRunId": run.id if run else None,
        "report": report_view(report) if report else None,
        "previousReport": previous,
        "suggestion": suggestion,
        "legal": legal_view,
        "closeType": review.closed_type,
        "closedAt": to_kst(review.closed_at),
        "allowedActions": state.actions_for(user),
    }
