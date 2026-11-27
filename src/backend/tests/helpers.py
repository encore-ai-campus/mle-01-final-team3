"""테스트에서 쓰는 요청·완료 통지 예시."""

from fastapi.testclient import TestClient

API = "/api/v1"
INTERNAL = "/internal/v1"

LAW = {"title": "식품 등의 표시·광고에 관한 법률", "reference": "제8조 제1항", "url": None,
       "lawText": "누구든지 식품등의 명칭·제조방법·성분 등에 관하여 질병의 예방·치료에 효능이 있는 것으로 인식할 우려가 있는 표시 또는 광고를 하여서는 아니 된다.",
       "noticeNo": None, "effectiveDate": None}  # fmt: skip
CASE = {"title": "일반식품 면역 기능성 표방 광고 (예시)", "summary": "일반식품에 면역력 개선 표현을 써 시정명령",
        "caseRef": None, "caseDate": None, "url": None}  # fmt: skip


def finding(decision: str = "UNSUITABLE", text: str = "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.", **kw) -> dict:
    unsuitable = decision == "UNSUITABLE"
    return {
        "sentenceId": "s1",
        "text": text,
        "decision": decision,
        "rationale": "일반식품은 면역력 개선 등 기능성을 표시할 수 없습니다." if unsuitable else "기준 위반 표현이 없습니다.",
        "violationCode": "3" if unsuitable else None,
        "sources": [LAW] if unsuitable else [],
        "referenceCases": [CASE] if unsuitable else [],
        "alternativeText": "맛과 원료 중심으로 표현해 보세요." if unsuitable else None,
        **kw,
    }


def report(decision: str = "UNSUITABLE", findings: list[dict] | None = None, **kw) -> dict:
    return {
        "decision": decision,
        "summary": "일반식품에 기능성 표현이 있습니다." if decision == "UNSUITABLE" else "위반 표현이 없습니다.",
        "improvementNote": "기능성 표현을 빼 주세요." if decision == "UNSUITABLE" else None,
        "findings": findings if findings is not None else [finding(decision)],
        **kw,
    }


SUGGESTION = {"text": "하루 한 포, 맛있게 즐기는 건강한 습관.", "rationale": "기능성 표현을 빼고 섭취 습관 중심으로 바꿨습니다."}
TEMP_ERROR = {"code": "SEARCH_FAILED", "message": "검색 서버 응답이 없습니다.", "retryable": True}
INPUT_ERROR = {"code": "INVALID_INPUT", "message": "첨부 파일을 읽을 수 없습니다.", "retryable": False}


def new_review(c: TestClient, title: str = "면역력 강화 음료 광고", **kw) -> tuple[str, str]:
    body = {"title": title, "productCategory": "GENERAL_FOOD", "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.", **kw}
    r = c.post(f"{API}/reviews", json=body)
    assert r.status_code == 202, r.text
    return r.json()["reviewId"], r.json()["runId"]


def complete(agent_http: TestClient, run_id: str, review_id: str, status: str = "SUCCEEDED", **body):
    return agent_http.post(
        f"{INTERNAL}/review-runs/{run_id}/completion",
        json={"schemaVersion": "1.0", "reviewId": review_id, "runStatus": status, **body},
    )


def finish(agent_http: TestClient, run_id: str, review_id: str, decision: str = "UNSUITABLE") -> dict:
    r = complete(agent_http, run_id, review_id, report=report(decision))
    assert r.status_code == 200, r.text
    return r.json()


def fail(agent_http: TestClient, run_id: str, review_id: str, error: dict = TEMP_ERROR) -> dict:
    r = complete(agent_http, run_id, review_id, "FAILED", error=error)
    assert r.status_code == 200, r.text
    return r.json()


def detail(c: TestClient, review_id: str) -> dict:
    r = c.get(f"{API}/reviews/{review_id}")
    assert r.status_code == 200, r.text
    return r.json()


def run_of(c: TestClient, run_id: str) -> dict:
    r = c.get(f"{API}/review-runs/{run_id}")
    assert r.status_code == 200, r.text
    return r.json()


def suggest(c: TestClient, agent_http: TestClient, review_id: str) -> str:
    """[AI 추천 요청] → 추천 문구 완료 통지까지. RA_SUGGEST runId를 돌려준다."""
    r = c.post(f"{API}/reviews/{review_id}/ra-runs")
    assert r.status_code == 202, r.text
    run_id = r.json()["runId"]
    assert complete(agent_http, run_id, review_id, suggestion=SUGGESTION).status_code == 200
    return run_id
