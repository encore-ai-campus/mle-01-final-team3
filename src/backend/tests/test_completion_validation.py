"""완료 통지 검증 규칙 (설계서 6장). 어기면 422 VALIDATION_ERROR와 fieldErrors."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import INTERNAL, SUGGESTION, TEMP_ERROR, complete, detail, finding, new_review, report


def fields(r) -> set[tuple[str, str]]:
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    return {(e["field"], e["code"]) for e in r.json()["error"]["fieldErrors"]}


@pytest.fixture
def started(mkt):
    return new_review(mkt)  # (reviewId, runId)


# ---------- 인증·대상 ----------


def test_requires_agent_token(started):
    rev, run = started
    body = {"schemaVersion": "1.0", "reviewId": rev, "runStatus": "FAILED", "error": TEMP_ERROR}
    r = TestClient(app).post(f"{INTERNAL}/review-runs/{run}/completion", json=body)
    assert r.status_code == 401
    r = TestClient(app, headers={"Authorization": "Bearer wrong"}).post(f"{INTERNAL}/review-runs/{run}/completion", json=body)
    assert r.status_code == 401


def test_unknown_run_or_review_mismatch_404(agent_http, started):
    rev, run = started
    assert complete(agent_http, "run_none", rev, "FAILED", error=TEMP_ERROR).status_code == 404
    assert complete(agent_http, run, "revw_other", "FAILED", error=TEMP_ERROR).status_code == 404


# ---------- 성공·실패 짝 ----------


def test_success_needs_report(agent_http, started):
    rev, run = started
    assert fields(complete(agent_http, run, rev)) == {("report", "REQUIRED")}


def test_success_with_error_is_invalid(agent_http, started):
    rev, run = started
    assert fields(complete(agent_http, run, rev, report=report(), error=TEMP_ERROR)) == {("error", "INVALID")}


def test_failure_needs_error_only(agent_http, started):
    rev, run = started
    assert fields(complete(agent_http, run, rev, "FAILED")) == {("error", "REQUIRED")}
    assert fields(complete(agent_http, run, rev, "FAILED", error=TEMP_ERROR, report=report())) == {("report", "INVALID")}


def test_suggest_needs_suggestion_not_report(mkt, agent_http, started):
    from tests.helpers import finish

    rev, run = started
    finish(agent_http, run, rev)
    ra = mkt.post("/api/v1/reviews/" + rev + "/ra-runs").json()["runId"]
    assert fields(complete(agent_http, ra, rev, report=report())) == {("suggestion", "REQUIRED"), ("report", "INVALID")}
    assert fields(complete(agent_http, ra, rev, suggestion={"text": "문구", "rationale": " "})) == {
        ("suggestion.rationale", "REQUIRED")
    }
    assert complete(agent_http, ra, rev, suggestion=SUGGESTION).status_code == 200


def test_screening_with_suggestion_is_invalid(agent_http, started):
    rev, run = started
    assert fields(complete(agent_http, run, rev, report=report(), suggestion=SUGGESTION)) == {("suggestion", "INVALID")}


def test_schema_version(agent_http, started):
    rev, run = started
    r = agent_http.post(f"{INTERNAL}/review-runs/{run}/completion",
                        json={"schemaVersion": "2.0", "reviewId": rev, "runStatus": "SUCCEEDED", "report": report()})  # fmt: skip
    assert fields(r) == {("schemaVersion", "INVALID")}


# ---------- 빈 값 ----------


def test_common_required(agent_http, started):
    rev, run = started
    r = agent_http.post(f"{INTERNAL}/review-runs/{run}/completion", json={"schemaVersion": " ", "reviewId": rev})
    assert fields(r) == {("schemaVersion", "REQUIRED"), ("runStatus", "REQUIRED")}


def test_report_required_fields(agent_http, started):
    rev, run = started
    r = complete(agent_http, run, rev, report={"decision": "UNSUITABLE", "summary": "", "findings": []})
    assert fields(r) == {("report.summary", "REQUIRED"), ("report.findings", "REQUIRED")}


def test_finding_required_fields(agent_http, started):
    rev, run = started
    f = finding()
    f.update(sentenceId="", rationale=None, sources=None)
    del f["referenceCases"]
    r = complete(agent_http, run, rev, report=report(findings=[f]))
    assert fields(r) == {
        ("report.findings[0].sentenceId", "REQUIRED"),
        ("report.findings[0].rationale", "REQUIRED"),
        ("report.findings[0].sources", "REQUIRED"),
        ("report.findings[0].referenceCases", "REQUIRED"),
    }


def test_source_and_case_required_fields(agent_http, started):
    rev, run = started
    f = finding(sources=[{"title": "법", "reference": " "}], referenceCases=[{"title": "", "summary": "요약"}])
    assert fields(complete(agent_http, run, rev, report=report(findings=[f]))) == {
        ("report.findings[0].sources[0].reference", "REQUIRED"),
        ("report.findings[0].referenceCases[0].title", "REQUIRED"),
    }


def test_nullable_field_blank_string_is_invalid(agent_http, started):
    rev, run = started
    r = complete(agent_http, run, rev, report=report(improvementNote="  "))
    assert fields(r) == {("report.improvementNote", "INVALID")}


def test_error_required_fields(agent_http, started):
    rev, run = started
    r = complete(agent_http, run, rev, "FAILED", error={"code": "X", "message": ""})
    assert fields(r) == {("error.message", "REQUIRED"), ("error.retryable", "REQUIRED")}


# ---------- 내용 규칙 ----------


def test_overall_decision_must_match_findings(agent_http, started):
    rev, run = started
    r = complete(agent_http, run, rev, report=report("SUITABLE", findings=[finding("SUITABLE"), finding("UNSUITABLE")]))
    assert fields(r) == {("report.decision", "INVALID")}


def test_unsuitable_needs_source(agent_http, started):
    rev, run = started
    r = complete(agent_http, run, rev, report=report(findings=[finding(sources=[])]))
    assert fields(r) == {("report.findings[0].sources", "REQUIRED")}


def test_violation_code_rules(agent_http, started):
    rev, run = started
    cases = [
        (finding(violationCode=None), "REQUIRED"),
        (finding(violationCode="99-가"), "INVALID"),
    ]
    for f, code in cases:
        assert fields(complete(agent_http, run, rev, report=report(findings=[f]))) == {
            ("report.findings[0].violationCode", code)
        }
    suitable_with_code = report("SUITABLE", findings=[finding("SUITABLE", violationCode="3")])
    assert fields(complete(agent_http, run, rev, report=suitable_with_code)) == {
        ("report.findings[0].violationCode", "INVALID")
    }


def test_valid_after_rejections(mkt, agent_http, started):
    """422를 받은 실행은 그대로 RUNNING이라 고쳐서 다시 보내면 저장된다."""
    rev, run = started
    complete(agent_http, run, rev, report=report(findings=[finding(sources=[])]))
    multi = report(findings=[finding("SUITABLE", sentenceId="s1"), finding("UNSUITABLE", sentenceId="s2")])
    assert complete(agent_http, run, rev, report=multi).status_code == 200
    assert [f["sentenceId"] for f in detail(mkt, rev)["report"]["findings"]] == ["s1", "s2"]
