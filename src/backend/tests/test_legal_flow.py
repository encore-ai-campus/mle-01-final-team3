"""법무 검토 요청 → 검토 시작 → 의견 전송 → 끝 처리, 그리고 알림. 설계서 3장·5장·6장."""

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import ActivityLog, LegalSubmission, Notification, ReviewRun
from tests.helpers import API, SUGGESTION, complete, detail, fail, finish, new_review, report, suggest


def suitable_review(mkt, agent_http, title="저당 에너지바 광고") -> tuple[str, str]:
    """적합 보고서까지 만든 검토 건. (reviewId, 보고서 runId)"""
    rid, run_id = new_review(mkt, title=title)
    finish(agent_http, run_id, rid, "SUITABLE")
    return rid, run_id


def send_to_legal(mkt, rid: str, report_run_id: str, **headers) -> dict:
    r = mkt.post(f"{API}/reviews/{rid}/legal-submissions", json={"reportRunId": report_run_id}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def notifications(db, user_id: str) -> list[Notification]:
    return list(db.scalars(select(Notification).where(Notification.user_id == user_id).order_by(Notification.id)))


def operations(db, user_id: str) -> list[str]:
    return list(db.scalars(select(ActivityLog.operation).where(ActivityLog.user_id == user_id).order_by(ActivityLog.id)))


# ---------- 전체 흐름 ----------


def test_full_legal_flow(mkt, legal, legal_b, agent_http, db):
    rid, run_id = suitable_review(mkt, agent_http)

    sub = send_to_legal(mkt, rid, run_id)
    assert sub["legalStatus"] == "PENDING" and sub["reportRunId"] == run_id and sub["sentAt"].endswith("+09:00")
    sid = sub["submissionId"]
    assert detail(mkt, rid)["allowedActions"] == []  # 검토 대기 중에는 버튼 없음
    # 법무팀 전체에 알림 (검토함 파란 불)
    for c in (legal, legal_b):
        n = notifications(db, c.user_id)
        assert [(x.type, x.menu, x.submission_id) for x in n] == [("SUBMISSION_RECEIVED", "INBOX", sid)]

    # 법무 상세: 상태를 바꾸지 않고, 검토 대기면 버튼 없음. 요청 시점 보고서
    r = legal.get(f"{API}/legal-submissions/{sid}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["legalStatus"] == "PENDING" and d["reviewer"] is None and d["allowedActions"] == []
    assert d["reportRunId"] == run_id and d["decision"] == "SUITABLE" and d["stage"] == "AI_SCREENING"
    assert d["channel"] == "DETAIL_PAGE" and d["mainIngredients"] == [] and d["sender"]["userId"] == mkt.user_id
    assert d["text"] == d["report"]["reviewedText"] and d["report"]["version"] == 1
    assert "REPORT_VIEWED" in operations(db, legal.user_id)

    # [검토 시작]: 먼저 누른 사람이 담당자. 두 번째 사람은 바뀌지 않고 읽기 전용
    r = legal.post(f"{API}/legal-submissions/{sid}/start")
    assert r.status_code == 200, r.text
    assert r.json()["legalStatus"] == "IN_REVIEW" and r.json()["reviewer"]["userId"] == legal.user_id
    assert r.json()["allowedActions"] == ["SEND_OPINION"] and r.json()["startedAt"]
    r = legal_b.post(f"{API}/legal-submissions/{sid}/start")
    assert r.status_code == 200 and r.json()["reviewer"]["userId"] == legal.user_id and r.json()["allowedActions"] == []
    again = legal.post(f"{API}/legal-submissions/{sid}/start").json()  # 같은 요청 반복도 200, 그대로
    assert again["startedAt"] == r.json()["startedAt"]

    # 의견 전송: 담당자가 아니면 403, 빈 의견 422
    assert legal_b.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "의견"}).status_code == 403
    r = legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "  "})
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"] == [{"field": "reason", "code": "REQUIRED"}]
    r = legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "‘에너지’ 표현은 근거가 필요합니다."})
    assert r.status_code == 200, r.text
    assert r.json()["legalStatus"] == "OPINION_SENT" and r.json()["decidedAt"] and r.json()["allowedActions"] == []
    # 이미 보낸 건은 거절
    assert legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "또"}).status_code == 409

    # 마케팅: 알림(전송 내역 파란 불)과 버튼
    n = notifications(db, mkt.user_id)
    assert [(x.type, x.menu) for x in n if x.type == "LEGAL_OPINION_SENT"] == [("LEGAL_OPINION_SENT", "SENT_LIST")]
    d = detail(mkt, rid)
    assert d["legal"]["legalStatus"] == "OPINION_SENT" and d["legal"]["reason"].startswith("‘에너지’")
    assert d["allowedActions"] == ["PUBLISH", "RUN_RA", "CANCEL"]

    # [게시 및 완료] → 끝. 다시 누르면 409 REVIEW_CLOSED
    r = mkt.post(f"{API}/reviews/{rid}/close", json={"closeType": "PUBLISHED"})
    assert r.status_code == 200, r.text
    assert r.json()["closeType"] == "PUBLISHED" and r.json()["closedAt"].endswith("+09:00")
    assert detail(mkt, rid)["allowedActions"] == []
    r = mkt.post(f"{API}/reviews/{rid}/close", json={"closeType": "PUBLISHED"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "REVIEW_CLOSED"

    # 목록에 반영
    row = mkt.get(f"{API}/reviews").json()["items"][0]
    assert row["stage"] == "LEGAL_REVIEW" and row["result"] == "PUBLISHED" and row["legalStatus"] == "OPINION_SENT"
    assert [op for op in operations(db, mkt.user_id) if op in ("LEGAL_SENT", "REVIEW_CLOSED")] == ["LEGAL_SENT", "REVIEW_CLOSED"]
    assert "LEGAL_OPINION_SENT" in operations(db, legal.user_id)


# ---------- 법무 검토 요청 규칙 ----------


def test_legal_request_rules(mkt, mkt_b, agent_http, db):
    bad, bad_run = new_review(mkt, title="부적합 광고")
    finish(agent_http, bad_run, bad, "UNSUITABLE")
    r = mkt.post(f"{API}/reviews/{bad}/legal-submissions", json={"reportRunId": bad_run})
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"  # 부적합은 요청 대상 아님

    rid, run_id = suitable_review(mkt, agent_http)
    r = mkt.post(f"{API}/reviews/{rid}/legal-submissions", json={"reportRunId": bad_run})  # 다른 건의 보고서
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"] == [{"field": "reportRunId", "code": "INVALID"}]
    r = mkt.post(f"{API}/reviews/{rid}/legal-submissions", json={})
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"][0]["field"] == "reportRunId"
    assert mkt_b.post(f"{API}/reviews/{rid}/legal-submissions", json={"reportRunId": run_id}).status_code == 403

    # 같은 키로 두 번 → 한 번만 요청, 같은 응답
    a = send_to_legal(mkt, rid, run_id, **{"Idempotency-Key": "send-1"})
    b = send_to_legal(mkt, rid, run_id, **{"Idempotency-Key": "send-1"})
    assert a == b
    # 키 없이 같은 보고서로 또 요청 → 409
    r = mkt.post(f"{API}/reviews/{rid}/legal-submissions", json={"reportRunId": run_id})
    assert r.status_code == 409
    assert len(db.scalars(select(LegalSubmission).where(LegalSubmission.review_id == rid)).all()) == 1


def test_resend_after_recheck_uses_new_report(mkt, legal, agent_http):
    """검토 의견 → AI 추천 → 재심의 적합 → 새 보고서로 다시 요청. 예전 요청 보고서로는 409."""
    rid, run_id = suitable_review(mkt, agent_http)
    sid = send_to_legal(mkt, rid, run_id)["submissionId"]
    legal.post(f"{API}/legal-submissions/{sid}/start")
    legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "수정 필요"})

    sug_run = suggest(mkt, agent_http, rid)
    r = mkt.post(f"{API}/reviews/{rid}/ra-runs/{sug_run}/recheck")
    re_run = r.json()["runId"]
    assert complete(agent_http, re_run, rid, report=report("SUITABLE")).status_code == 200

    r = mkt.post(f"{API}/reviews/{rid}/legal-submissions", json={"reportRunId": run_id})
    assert r.status_code == 409  # 최신 보고서가 아님
    sub2 = send_to_legal(mkt, rid, re_run)
    d = legal.get(f"{API}/legal-submissions/{sub2['submissionId']}").json()
    assert d["stage"] == "RA_RECHECK" and d["report"]["version"] == 2 and d["text"] == SUGGESTION["text"]
    # 예전 요청은 요청 시점 그대로
    old = legal.get(f"{API}/legal-submissions/{sid}").json()
    assert old["report"]["version"] == 1 and old["legalStatus"] == "OPINION_SENT"


# ---------- 끝 처리 규칙 ----------


def test_close_rules(mkt, mkt_b, agent_http):
    ok, ok_run = suitable_review(mkt, agent_http, title="적합 광고")
    assert mkt_b.post(f"{API}/reviews/{ok}/close", json={"closeType": "ENDED"}).status_code == 403  # 작성자만
    r = mkt.post(f"{API}/reviews/{ok}/close", json={"closeType": "PUBLISHED"})  # 검토 의견 전에는 게시 불가
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"
    assert mkt.post(f"{API}/reviews/{ok}/close", json={"closeType": "CANCELED"}).status_code == 409  # 적합은 취소 대신 종료
    assert mkt.post(f"{API}/reviews/{ok}/close", json={"closeType": "DONE"}).status_code == 422
    r = mkt.post(f"{API}/reviews/{ok}/close", json={"closeType": "ENDED"})
    assert r.status_code == 200 and r.json()["closeType"] == "ENDED"

    bad, bad_run = new_review(mkt, title="부적합 광고")
    finish(agent_http, bad_run, bad, "UNSUITABLE")
    assert mkt.post(f"{API}/reviews/{bad}/close", json={"closeType": "ENDED"}).status_code == 409
    assert mkt.post(f"{API}/reviews/{bad}/close", json={"closeType": "CANCELED"}).status_code == 200

    # 재시도할 수 없는 오류로 첫 심의가 실패해 보고서가 없는 건도 취소할 수 있다
    broken, broken_run = new_review(mkt, title="첨부 오류 광고")
    fail(agent_http, broken_run, broken, {"code": "INVALID_INPUT", "message": "파일 오류", "retryable": False})
    assert mkt.post(f"{API}/reviews/{broken}/close", json={"closeType": "CANCELED"}).status_code == 200

    # 실행 중이면 아무것도 못 한다
    running, _ = new_review(mkt, title="실행 중 광고")
    assert mkt.post(f"{API}/reviews/{running}/close", json={"closeType": "CANCELED"}).status_code == 409


def test_legal_endpoints_need_legal_role(mkt, legal, agent_http):
    rid, run_id = suitable_review(mkt, agent_http)
    sid = send_to_legal(mkt, rid, run_id)["submissionId"]
    assert mkt.get(f"{API}/legal-submissions/{sid}").status_code == 403
    assert mkt.post(f"{API}/legal-submissions/{sid}/start").status_code == 403
    assert legal.get(f"{API}/legal-submissions/sub_none").status_code == 404
    assert legal.post(f"{API}/reviews/{rid}/close", json={"closeType": "ENDED"}).status_code == 403


def test_opinion_idempotency(mkt, legal, agent_http, db):
    rid, run_id = suitable_review(mkt, agent_http)
    sid = send_to_legal(mkt, rid, run_id)["submissionId"]
    legal.post(f"{API}/legal-submissions/{sid}/start")
    h = {"Idempotency-Key": "op-1"}
    a = legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "의견"}, headers=h)
    b = legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "의견"}, headers=h)
    assert a.status_code == b.status_code == 200 and a.json() == b.json()
    assert len([n for n in notifications(db, mkt.user_id) if n.type == "LEGAL_OPINION_SENT"]) == 1


# ---------- 재심의 문구 (review_runs.input_text) ----------


def test_recheck_run_keeps_input_text_and_retry_copies_it(mkt, agent_http, agent, db):
    rid, run_id = new_review(mkt)
    finish(agent_http, run_id, rid, "UNSUITABLE")
    sug_run = suggest(mkt, agent_http, rid)
    re_run = mkt.post(f"{API}/reviews/{rid}/ra-runs/{sug_run}/recheck").json()["runId"]
    assert db.get(ReviewRun, re_run).input_text == SUGGESTION["text"]
    assert agent.last()["text"] == SUGGESTION["text"] and agent.last()["channel"] == "DETAIL_PAGE"

    fail(agent_http, re_run, rid)
    retry_run = mkt.post(f"{API}/review-runs/{re_run}/retry").json()["runId"]
    db.expire_all()
    assert db.get(ReviewRun, retry_run).input_text == SUGGESTION["text"]
    assert agent.last()["text"] == SUGGESTION["text"]


# ---------- 알림 ----------


def test_notifications_summary_list_and_badges(mkt, legal, agent_http):
    rid, run_id = suitable_review(mkt, agent_http)
    sid = send_to_legal(mkt, rid, run_id)["submissionId"]

    s = legal.get(f"{API}/notifications/summary").json()
    assert s == {"unreadCount": 1, "menuBadges": {"inbox": True, "sentList": False}}
    items = legal.get(f"{API}/notifications").json()
    assert items["nextCursor"] is None and len(items["items"]) == 1
    n = items["items"][0]
    assert n["type"] == "SUBMISSION_RECEIVED" and n["target"] == sid and n["readAt"] is None
    assert n["createdAt"].endswith("+09:00")

    # 메뉴에 들어가면 그 메뉴 파란 불만 꺼지고, 알림은 안 읽은 채로 남는다
    r = legal.post(f"{API}/notifications/menu-seen", json={"menu": "INBOX"})
    assert r.status_code == 200 and r.json() == {"unreadCount": 1, "menuBadges": {"inbox": False, "sentList": False}}
    # [모두 읽음]
    assert legal.post(f"{API}/notifications/read-all").json() == {"unreadCount": 0}
    assert legal.get(f"{API}/notifications").json()["items"][0]["readAt"] is not None
    assert legal.post(f"{API}/notifications/menu-seen", json={"menu": "OTHER"}).status_code == 422

    # 마케팅: 검토 의견 알림은 '법무팀 전송 내역' 파란 불, target은 reviewId
    legal.post(f"{API}/legal-submissions/{sid}/start")
    legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "의견"})
    s = mkt.get(f"{API}/notifications/summary").json()
    assert s["menuBadges"] == {"inbox": False, "sentList": True} and s["unreadCount"] == 1
    assert mkt.get(f"{API}/notifications").json()["items"][0]["target"] == rid


def test_notifications_newest_first_with_cursor(mkt, agent_http):
    for i in range(3):
        rid, run_id = new_review(mkt, title=f"광고{i}")
        finish(agent_http, run_id, rid, "UNSUITABLE")
        suggest(mkt, agent_http, rid)  # 작성자에게 RA_SUGGESTED 알림
    first = mkt.get(f"{API}/notifications", params={"limit": 2}).json()
    assert len(first["items"]) == 2 and first["nextCursor"]
    second = mkt.get(f"{API}/notifications", params={"limit": 2, "cursor": first["nextCursor"]}).json()
    msgs = [n["message"] for n in first["items"] + second["items"]]
    assert [m.split(" · ")[0] for m in msgs] == ["광고2", "광고1", "광고0"]
    assert second["nextCursor"] is None


# ---------- PDF ----------


def pdf_text(content: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    return "".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)


def test_report_pdf(mkt, mkt_b, legal, agent_http):
    rid, run_id = new_review(mkt, title="면역 <음료> & 광고")
    assert mkt.get(f"{API}/reviews/{rid}/report.pdf").status_code == 404  # 보고서 전
    finish(agent_http, run_id, rid, "SUITABLE")

    r = mkt_b.get(f"{API}/reviews/{rid}/report.pdf")  # 팀 공유: 다른 작성자도 받는다
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert "filename*=UTF-8''" in r.headers["content-disposition"] and "v1.pdf" in r.headers["content-disposition"]
    assert "면역 <음료> & 광고 검토 보고서" in pdf_text(r.content)  # 특수문자도 그대로

    sid = send_to_legal(mkt, rid, run_id)["submissionId"]
    legal.post(f"{API}/legal-submissions/{sid}/start")
    legal.post(f"{API}/legal-submissions/{sid}/opinion", json={"reason": "표현 근거를 첨부해 주세요."})
    r = legal.get(f"{API}/legal-submissions/{sid}/report.pdf")
    assert r.status_code == 200 and "표현 근거를 첨부해 주세요." in pdf_text(r.content)
    assert mkt.get(f"{API}/legal-submissions/{sid}/report.pdf").status_code == 403
