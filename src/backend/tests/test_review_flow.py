"""정상 흐름: 검토 요청 → Agent 작업 요청 → 완료 통지 → 보고서 조회, AI 추천 요청 → 재심의 → 버전 +1."""

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.ids import new_id
from app.core.security import utcnow
from app.models import ActivityLog, LegalSubmission, Notification, Report
from tests.helpers import API, SUGGESTION, complete, detail, finish, new_review, report, run_of, suggest


def test_create_review_returns_202_and_dispatches_job(mkt, agent):
    r = mkt.post(f"{API}/reviews", json={"title": "면역력 음료", "productCategory": "GENERAL_FOOD", "channel": "SNS",
                                          "mainIngredients": ["홍삼", "비타민C"], "text": "면역력 쑥쑥"})  # fmt: skip
    assert r.status_code == 202
    body = r.json()
    assert body["stage"] == "AI_SCREENING" and body["runStatus"] == "QUEUED"
    assert r.headers["Location"] == f"{API}/review-runs/{body['runId']}"

    # 응답 뒤 Agent에 작업 요청 1번 → 202 → RUNNING
    job = agent.last()
    assert job == {
        "schemaVersion": "1.0", "runId": body["runId"], "reviewId": body["reviewId"], "stage": "AI_SCREENING",
        "title": "면역력 음료", "productCategory": "GENERAL_FOOD", "channel": "SNS", "mainIngredients": ["홍삼", "비타민C"],
        "text": "면역력 쑥쑥", "attachments": [],
        "baseReportRunId": None, "baseReport": None, "legalOpinion": None,
    }  # fmt: skip
    run = run_of(mkt, body["runId"])
    assert run["runStatus"] == "RUNNING" and run["attempt"] == 1
    assert run["startedAt"] and run["finishedAt"] is None and run["error"] is None
    assert run["updatedAt"].endswith("+09:00")

    d = detail(mkt, body["reviewId"])
    assert d["runStatus"] == "RUNNING" and d["latestRunId"] == body["runId"]
    assert d["report"] is None and d["allowedActions"] == []  # 실행 중 버튼 잠금


def test_blank_fields_are_422(mkt):
    r = mkt.post(f"{API}/reviews", json={"title": " ", "productCategory": "GENERAL_FOOD"})
    assert r.status_code == 422
    fields = {(e["field"], e["code"]) for e in r.json()["error"]["fieldErrors"]}
    assert fields == {("title", "REQUIRED"), ("text", "REQUIRED"), ("channel", "REQUIRED")}


def test_channel_and_ingredients_rules(mkt):
    body = {"title": "t", "productCategory": "GENERAL_FOOD", "text": "x"}
    r = mkt.post(f"{API}/reviews", json={**body, "channel": "TV"})  # DETAIL_PAGE·SNS·BANNER만
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"][0]["field"] == "channel"
    r = mkt.post(f"{API}/reviews", json={**body, "channel": "SNS", "mainIngredients": ["홍삼", " "]})
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"][0]["field"] == "mainIngredients[1]"
    # 주요 원료는 생략하면 빈 배열
    rid = mkt.post(f"{API}/reviews", json={**body, "channel": "SNS"}).json()["reviewId"]
    d = detail(mkt, rid)
    assert d["channel"] == "SNS" and d["mainIngredients"] == []


def test_title_over_200_is_422(mkt):
    body = {"productCategory": "GENERAL_FOOD", "channel": "DETAIL_PAGE", "text": "문구"}
    r = mkt.post(f"{API}/reviews", json={**body, "title": "가" * 201})
    assert r.status_code == 422
    assert [(e["field"], e["code"]) for e in r.json()["error"]["fieldErrors"]] == [("title", "INVALID")]
    assert mkt.post(f"{API}/reviews", json={**body, "title": "가" * 200}).status_code == 202


def test_only_marketing_can_request(legal):
    r = legal.post(f"{API}/reviews", json={"title": "a", "productCategory": "GENERAL_FOOD", "text": "b"})
    assert r.status_code == 403


def test_unsuitable_report_v1(mkt, agent_http):
    rev, run = new_review(mkt)
    res = finish(agent_http, run, rev, "UNSUITABLE")
    assert res["runStatus"] == "SUCCEEDED" and res["finishedAt"]

    d = detail(mkt, rev)
    assert d["runStatus"] == "SUCCEEDED"
    rep = d["report"]
    assert rep["runId"] == run and rep["stage"] == "AI_SCREENING" and rep["version"] == 1
    assert rep["reviewedText"] == d["text"]  # AI 심의는 원문
    assert rep["decision"] == "UNSUITABLE" and rep["findings"][0]["violationCode"] == "3"
    assert rep["findings"][0]["sources"][0]["reference"] == "제8조 제1항"
    assert d["previousReport"] is None and d["suggestion"] is None and d["legal"] is None
    assert d["allowedActions"] == ["RUN_RA", "CANCEL"]


def test_suitable_report_actions(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "SUITABLE")
    assert detail(mkt, rev)["allowedActions"] == ["SEND_TO_LEGAL", "END"]


def test_report_view_logs_activity_every_time(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    detail(mkt, rev)
    detail(mkt, rev)
    with SessionLocal() as db:
        ops = db.scalars(select(ActivityLog.operation).where(ActivityLog.user_id == mkt.user_id)).all()
    assert ops.count("REPORT_VIEWED") == 2 and ops.count("REVIEW_REQUESTED") == 1


def test_other_marketer_sees_report_without_actions(mkt, mkt_b, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    assert detail(mkt_b, rev)["allowedActions"] == []
    r = mkt_b.post(f"{API}/reviews/{rev}/ra-runs")
    assert r.status_code == 403


def test_unknown_review_404(mkt):
    r = mkt.get(f"{API}/reviews/revw_none")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_ra_suggest_then_recheck_bumps_version(mkt, agent, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "UNSUITABLE")

    # [AI 추천 요청] → RA_SUGGEST: 직전 보고서를 함께 보낸다
    r = mkt.post(f"{API}/reviews/{rev}/ra-runs")
    assert r.status_code == 202 and r.json()["stage"] == "RA_SUGGEST"
    sug_run = r.json()["runId"]
    job = agent.last()
    assert job["stage"] == "RA_SUGGEST" and job["baseReportRunId"] == run
    assert job["baseReport"]["version"] == 1 and job["legalOpinion"] is None
    assert detail(mkt, rev)["allowedActions"] == []  # 실행 중

    # 추천 문구 도착 → 보고서는 그대로(v1), 확인 팝업 버튼만
    assert complete(agent_http, sug_run, rev, suggestion=SUGGESTION).status_code == 200
    d = detail(mkt, rev)
    assert d["report"]["version"] == 1 and d["report"]["runId"] == run
    assert d["suggestion"]["runId"] == sug_run and d["suggestion"]["text"] == SUGGESTION["text"]
    assert d["suggestion"]["rationale"] == SUGGESTION["rationale"] and d["suggestion"]["createdAt"]
    assert d["allowedActions"] == ["RECHECK_SUGGESTION", "DISMISS_SUGGESTION"]

    # [재심의] → RA_RECHECK: 문구 자리에 추천 문구
    r = mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/recheck")
    assert r.status_code == 202 and r.json()["stage"] == "RA_RECHECK"
    recheck_run = r.json()["runId"]
    assert agent.last()["text"] == SUGGESTION["text"] and agent.last()["baseReportRunId"] == run
    assert detail(mkt, rev)["suggestion"] is None

    # 재심의 적합 → v2, reviewedText = 추천 문구, 이전 문구 = v1
    rep = report("SUITABLE")
    rep["findings"][0]["text"] = SUGGESTION["text"]
    assert complete(agent_http, recheck_run, rev, report=rep).status_code == 200
    d = detail(mkt, rev)
    assert d["report"]["version"] == 2 and d["report"]["stage"] == "RA_RECHECK"
    assert d["report"]["reviewedText"] == SUGGESTION["text"]
    assert d["previousReport"] == {"version": 1, "decision": "UNSUITABLE", "reviewedText": d["text"]}
    assert d["allowedActions"] == ["SEND_TO_LEGAL", "END"]

    with SessionLocal() as db:
        types = db.scalars(select(Notification.type).where(Notification.user_id == mkt.user_id)).all()
    assert sorted(types) == ["RA_COMPLETED", "RA_SUGGESTED"]


def test_recheck_twice_is_409(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    assert mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/recheck").status_code == 202
    r = mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/recheck")
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"


def test_dismiss_restores_previous_actions(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    r = mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/dismiss")
    assert r.status_code == 200
    d = r.json()
    assert d["suggestion"] is None and d["report"]["version"] == 1
    assert d["allowedActions"] == ["RUN_RA", "CANCEL"]
    # 이미 [닫기]한 문구
    assert mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/dismiss").status_code == 409
    assert mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/recheck").status_code == 409
    # 다시 AI 추천 요청 가능 (횟수 제한 없음)
    assert mkt.post(f"{API}/reviews/{rev}/ra-runs").status_code == 202


def test_suggestion_of_other_review_is_404(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    other, other_run = new_review(mkt, "다른 광고")
    assert mkt.post(f"{API}/reviews/{other}/ra-runs/{sug_run}/dismiss").status_code == 404


def test_ra_run_not_allowed_when_suitable(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "SUITABLE")
    r = mkt.post(f"{API}/reviews/{rev}/ra-runs")
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"


def test_ra_run_not_allowed_while_running(mkt):
    rev, _ = new_review(mkt)
    assert mkt.post(f"{API}/reviews/{rev}/ra-runs").status_code == 409


def _send_to_legal_with_opinion(review_id: str, report_run_id: str, author_id: str, reason: str) -> None:
    """법무 흐름은 다른 담당 범위라 DB에 직접 넣는다."""
    with SessionLocal() as db:
        now = utcnow()
        db.add(LegalSubmission(id=new_id(db, "sub"), review_id=review_id, report_run_id=report_run_id,
                               sender_id=author_id, status="OPINION_SENT", reason=reason, sent_at=now,
                               decided_at=now))  # fmt: skip
        db.commit()


def test_legal_opinion_actions_and_suggest_payload(mkt, agent, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "SUITABLE")
    _send_to_legal_with_opinion(rev, run, mkt.user_id, "‘면역력’ 표현은 근거가 필요합니다.")
    d = detail(mkt, rev)
    assert d["legal"]["legalStatus"] == "OPINION_SENT" and d["legal"]["reason"].startswith("‘면역력’")
    assert d["allowedActions"] == ["PUBLISH", "RUN_RA", "CANCEL"]

    assert mkt.post(f"{API}/reviews/{rev}/ra-runs").status_code == 202
    assert agent.last()["legalOpinion"] == "‘면역력’ 표현은 근거가 필요합니다."


def test_idempotency_key_returns_same_run(mkt, agent):
    body = {"title": "중복 클릭 광고", "productCategory": "GENERAL_FOOD", "channel": "BANNER", "text": "문구"}
    h = {"Idempotency-Key": "k-1"}
    a = mkt.post(f"{API}/reviews", json=body, headers=h)
    b = mkt.post(f"{API}/reviews", json=body, headers=h)
    assert a.status_code == b.status_code == 202
    assert a.json() == b.json() and b.headers["Location"] == a.headers["Location"]
    assert len(agent.jobs) == 1  # 작업 요청도 한 번만
    c = mkt.post(f"{API}/reviews", json={**body, "text": "다른 문구"}, headers=h)
    assert c.status_code == 409


def test_report_is_stored_once_per_run(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    with SessionLocal() as db:
        assert len(db.scalars(select(Report).where(Report.review_id == rev)).all()) == 1
