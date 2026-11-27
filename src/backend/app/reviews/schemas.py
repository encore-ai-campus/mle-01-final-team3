"""검토 흐름 요청 모델. JSON 필드는 camelCase (CamelModel).

- 검토 요청 (POST /api/v1/reviews)
- Agent 완료 통지 (POST /internal/v1/review-runs/{runId}/completion), 설계서 6장 '연동 방향'

빈 값 규칙 (설계서 6장): 필드 누락·null·빈 문자열·공백만 있는 문자열은 빈 값이다.
필수 필드가 빈 값이면 422 VALIDATION_ERROR, fieldErrors code=REQUIRED.
null을 허용하는 필드에 빈 문자열·공백을 보내면 INVALID (없으면 null로 보낸다).
"""

from typing import Annotated, Literal

from pydantic import AfterValidator, Field

from app.core.schemas import CamelModel, Text

ProductCategory = Literal["HEALTH_FUNCTIONAL_FOOD", "GENERAL_FOOD", "CHILDREN_PREFERRED_FOOD"]
Channel = Literal["DETAIL_PAGE", "SNS", "BANNER"]  # 게시 채널: 상세페이지·SNS·배너
Decision = Literal["SUITABLE", "UNSUITABLE"]

# DB 칼럼 길이를 넘는 값은 저장 단계에서 500이 나므로 입력에서 422(INVALID)로 막는다.
TITLE_MAX = 200  # reviews.title String(200)
ERROR_CODE_MAX = 50  # review_runs.error_code String(50)


def _no_blank(v: str | None) -> str | None:
    if v is not None and not v.strip():
        raise ValueError("빈 문자열 대신 null을 보내야 합니다")
    return v


# null을 허용하는 문자열. 빈 문자열·공백은 받지 않는다.
OptText = Annotated[str | None, AfterValidator(_no_blank)]


# ---------- 검토 요청 ----------


class ReviewCreate(CamelModel):
    title: Annotated[Text, Field(max_length=TITLE_MAX)]  # 제품명
    product_category: ProductCategory
    channel: Channel  # 게시 채널 (필수)
    main_ingredients: list[Text] = []  # 주요 원료명 (선택). 빈 문자열 원료는 422
    text: Text  # 광고 문구 원문
    attachment_ids: list[str] = []  # POST /attachments로 올린 파일 ID


# ---------- Agent 완료 통지 ----------


class Source(CamelModel):
    """출처(근거 조항)."""

    title: Text
    reference: Text  # 조항 (예: 제8조 제1항)
    url: OptText = None
    law_text: OptText = None  # 근거 법령 조문 원문
    notice_no: OptText = None  # 고시 발령번호. 법률·시행령이면 null
    effective_date: OptText = None  # 시행일 YYYY-MM-DD


class ReferenceCase(CamelModel):
    """참고 사례."""

    title: Text
    summary: Text
    case_ref: OptText = None
    case_date: OptText = None
    url: OptText = None


class Finding(CamelModel):
    """문장별 결과."""

    sentence_id: Text
    text: Text  # 판정한 문장. 재심의 보고서에서는 AI 추천 문구
    decision: Decision
    rationale: Text  # 판단 근거
    violation_code: OptText = None  # 부적합 문장은 부록 D 코드 필수, 적합 문장은 null (completion.py에서 검사)
    sources: list[Source]  # 없으면 []. 부적합 문장은 1개 이상
    reference_cases: list[ReferenceCase]  # 없으면 []
    alternative_text: OptText = None  # 대안 문구 예시


class ReportBody(CamelModel):
    """Agent가 보내는 보고서. version·reviewedText는 백엔드가 채우므로 받지 않는다."""

    decision: Decision
    summary: Text
    improvement_note: OptText = None
    findings: Annotated[list[Finding], Field(min_length=1)]


class SuggestionBody(CamelModel):
    """RA_SUGGEST 성공 때 report 대신 보내는 추천 문구 (판정 없음)."""

    text: Text
    rationale: Text


class RunError(CamelModel):
    code: Annotated[Text, Field(max_length=ERROR_CODE_MAX)]
    message: Text
    retryable: bool


class RunCompletion(CamelModel):
    """성공이면 report(RA_SUGGEST는 suggestion), 실패면 error만 보낸다."""

    schema_version: Text
    review_id: Text
    run_status: Literal["SUCCEEDED", "FAILED"]
    report: ReportBody | None = None
    suggestion: SuggestionBody | None = None
    error: RunError | None = None
