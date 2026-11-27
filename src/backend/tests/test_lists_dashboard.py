"""검토함 목록(GET /reviews, GET /legal-submissions)과 대시보드(GET /dashboard). 설계서 5장.

법무 요청 행은 상태·시각을 마음대로 맞추려고 DB에 직접 넣는다. API로 하는 흐름은 test_legal_flow.py에 있다.
"""

from datetime import timedelta

from sqlalchemy import update

from app.core.db import SessionLocal
from app.core.ids import new_id
from app.core.security import utcnow
from app.models import LegalSubmission, Report, Review, ReviewRun
from tests.helpers import API, finish, new_review, suggest


def age_run(run_id: str, seconds: int = 181) -> None:
    with SessionLocal() as db:
        db.execute(
            update(ReviewRun).where(ReviewRun.id == run_id).values(created_at=ReviewRun.created_at - timedelta(seconds=seconds))
        )
        db.commit()


def add_legal(review_id: str, report_run_id: str, sender_id: str, status: str = "PENDING", reviewer_id: str | None = None,
              decided_ago: timedelta | None = None) -> str:  # fmt: skip
    now = utcnow()
    with SessionLocal() as db:
        sub_id = new_id(db, "sub")
        db.add(LegalSubmission(
            id=sub_id, review_id=review_id, report_run_id=report_run_id, sender_id=sender_id, reviewer_id=reviewer_id,
            status=status, reason="의견" if status == "OPINION_SENT" else None, sent_at=now,
            started_at=now if reviewer_id else None,
            decided_at=(now - decided_ago) if decided_ago is not None else None,
        ))  # fmt: skip
        db.commit()
    return sub_id


def items(c, path: str = "/reviews", **params) -> list[dict]:
    r = c.get(f"{API}{path}", params=params)
    assert r.status_code == 200, r.text
    return r.json()["items"]


def by_id(rows: list[dict], key: str = "reviewId") -> dict:
    return {row[key]: row for row in rows}


# ---------- 마케팅 검토함 (view=ALL) ----------


def test_all_view_rows(mkt, mkt_b, agent_http):
    a, run_a = new_review(mkt, title="적합 광고")
    finish(agent_http, run_a, a, "SUITABLE")
    b, run_b = new_review(mkt, title="부적합 광고")
    finish(agent_http, run_b, b, "UNSUITABLE")
    c, run_c = new_review(mkt, title="실행 중 광고")

    rows = items(mkt)
    assert [r["reviewId"] for r in rows] == [c, b, a]  # updatedAt 최신순
    ra, rb, rc = by_id(rows)[a], by_id(rows)[b], by_id(rows)[c]
    assert ra["stage"] == "AI_SCREENING" and ra["decision"] == "SUITABLE" and ra["result"] == "SUITABLE"
    assert ra["version"] == 1 and ra["reportRunId"] == run_a and ra["legalStatus"] == "NOT_SENT"
    assert ra["allowedActions"] == ["SEND_TO_LEGAL", "END"]
    assert ra["author"] == {"userId": mkt.user_id, "name": "마케팅A"}
    assert ra["createdAt"].endswith("+09:00") and ra["submissionId"] is None and ra["sentAt"] is None
    assert rb["legalStatus"] is None and rb["allowedActions"] == ["RUN_RA", "CANCEL"]  # 부적합은 요청 대상 아님
    assert rc["stage"] == "AI_SCREENING" and rc["runStatus"] == "RUNNING" and rc["latestRunId"] == run_c
    assert rc["version"] is None and rc["decision"] is None and rc["result"] is None and rc["allowedActions"] == []

    # 다른 작성자에게는 같은 행이지만 버튼이 없다
    other = items(mkt_b)
    assert len(other) == 3 and all(r["allowedActions"] == [] for r in other)


def test_all_view_filters(mkt, mkt_b, agent_http):
    a, run_a = new_review(mkt, title="면역 음료 광고")
    finish(agent_http, run_a, a, "SUITABLE")
    b, run_b = new_review(mkt, title="다이어트 젤리", productCategory="HEALTH_FUNCTIONAL_FOOD")
    finish(agent_http, run_b, b, "UNSUITABLE")

    assert [r["reviewId"] for r in items(mkt, q="면역")] == [a]
    assert [r["reviewId"] for r in items(mkt, productCategory="HEALTH_FUNCTIONAL_FOOD")] == [b]
    assert [r["reviewId"] for r in items(mkt, decision="SUITABLE")] == [a]
    assert [r["reviewId"] for r in items(mkt, result="UNSUITABLE")] == [b]
    assert [r["reviewId"] for r in items(mkt, legalStatus="NOT_SENT")] == [a]
    assert [r["reviewId"] for r in items(mkt, action="RUN_RA")] == [b]
    assert [r["reviewId"] for r in items(mkt, author=mkt.user_id, decision="UNSUITABLE")] == [b]  # AND
    assert len(items(mkt, author="ME")) == 2
    assert items(mkt_b, author="ME") == []
    assert items(mkt_b, action="RUN_RA") == []  # 버튼은 작성자에게만
    assert mkt.get(f"{API}/reviews", params={"stage": "WRONG"}).status_code == 400  # 잘못된 조회 조건 = INVALID_QUERY


def test_legal_request_and_opinion_shown_in_lists(mkt, agent_http):
    a, run_a = new_review(mkt, title="적합 광고")
    finish(agent_http, run_a, a, "SUITABLE")
    sub = add_legal(a, run_a, mkt.user_id)

    row = by_id(items(mkt))[a]
    assert row["stage"] == "LEGAL_REVIEW" and row["legalStatus"] == "PENDING" and row["submissionId"] == sub
    assert row["sentAt"] and row["allowedActions"] == []
    assert [r["reviewId"] for r in items(mkt, stage="LEGAL_REVIEW")] == [a]

    sent = items(mkt, view="SENT")
    assert len(sent) == 1
    assert sent[0]["submissionId"] == sub and sent[0]["stage"] == "AI_SCREENING" and sent[0]["legalStatus"] == "PENDING"

    with SessionLocal() as db:
        s = db.get(LegalSubmission, sub)
        s.status, s.decided_at = "OPINION_SENT", utcnow()
        db.commit()
    row = by_id(items(mkt))[a]
    assert row["result"] == "LEGAL_OPINION_SENT" and row["decidedAt"]
    assert row["allowedActions"] == ["PUBLISH", "RUN_RA", "CANCEL"]
    assert items(mkt, view="SENT")[0]["result"] == "LEGAL_OPINION_SENT"


def test_closed_review_result_is_close_type(mkt, agent_http):
    a, run_a = new_review(mkt)
    finish(agent_http, run_a, a, "SUITABLE")
    with SessionLocal() as db:
        r = db.get(Review, a)
        r.closed_type, r.closed_at = "ENDED", utcnow()
        db.commit()
    row = items(mkt)[0]
    assert row["result"] == "ENDED" and row["closeType"] == "ENDED" and row["closedAt"] and row["allowedActions"] == []
    assert [x["reviewId"] for x in items(mkt, result="ENDED")] == [a]


def test_list_pagination_and_cursor(mkt):
    ids = [new_review(mkt, title=f"광고 {i}")[0] for i in range(3)]
    r1 = mkt.get(f"{API}/reviews", params={"limit": 2}).json()
    assert [x["reviewId"] for x in r1["items"]] == ids[::-1][:2] and r1["nextCursor"]
    r2 = mkt.get(f"{API}/reviews", params={"limit": 2, "cursor": r1["nextCursor"]}).json()
    assert [x["reviewId"] for x in r2["items"]] == [ids[0]] and r2["nextCursor"] is None

    bad = mkt.get(f"{API}/reviews", params={"limit": 2, "cursor": r1["nextCursor"], "q": "광고"})
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "INVALID_CURSOR"  # 조건이 바뀜
    assert mkt.get(f"{API}/reviews", params={"cursor": "엉터리"}).json()["error"]["code"] == "INVALID_CURSOR"
    assert mkt.get(f"{API}/reviews", params={"limit": 101}).status_code == 400


def test_list_expires_timed_out_runs(mkt):
    rev, run = new_review(mkt)
    age_run(run)
    row = items(mkt)[0]
    assert row["runStatus"] == "FAILED" and row["allowedActions"] == ["RETRY_RUN"]
    with SessionLocal() as db:
        assert db.get(ReviewRun, run).error_code == "RUN_TIMEOUT"  # 목록 조회로 확정·저장됨


def test_role_guard(mkt, legal, admin):
    assert legal.get(f"{API}/reviews").status_code == 403
    assert mkt.get(f"{API}/legal-submissions").status_code == 403
    assert admin.get(f"{API}/dashboard").status_code == 403


# ---------- 마케팅 대시보드 ----------


def test_marketing_dashboard(mkt, mkt_b, agent_http):
    a, run_a = new_review(mkt, title="적합")
    finish(agent_http, run_a, a, "SUITABLE")
    b, run_b = new_review(mkt, title="부적합")
    finish(agent_http, run_b, b, "UNSUITABLE")
    c, run_c = new_review(mkt, title="추천 확인")
    finish(agent_http, run_c, c, "UNSUITABLE")
    suggest(mkt, agent_http, c)  # 확인 대기 추천 문구 → '추천 문구 확인' 카드로 옮겨 감
    d, run_d = new_review(mkt, title="의견 도착")
    finish(agent_http, run_d, d, "SUITABLE")
    add_legal(d, run_d, mkt.user_id, "OPINION_SENT", decided_ago=timedelta(0))
    e, run_e = new_review(mkt_b, title="다른 사람 적합")
    finish(agent_http, run_e, e, "SUITABLE")

    r = mkt.get(f"{API}/dashboard", params={"recentLimit": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "MARKETING" and body["asOf"].endswith("+09:00")
    assert body["summary"] == {"completedReviews": 5, "raReviews": 1, "legalSentReviews": 1}
    assert body["tasks"] == {"sendToLegal": 1, "unsuitableToAct": 1, "opinionToCheck": 1, "suggestionToCheck": 1}
    assert [x["reviewId"] for x in body["recentReports"]] == [x["reviewId"] for x in items(mkt)[:3]]

    # 카드 건수 = 연결된 목록 건수
    assert len(items(mkt, author="ME", decision="SUITABLE", legalStatus="NOT_SENT", action="SEND_TO_LEGAL")) == 1
    assert len(items(mkt, author="ME", decision="UNSUITABLE", action="RUN_RA")) == 1
    assert mkt.get(f"{API}/dashboard", params={"recentLimit": 21}).status_code == 400


def test_marketing_summary_counts_this_month_only(mkt, agent_http):
    """윗칸은 이번 달(한국시간) 건수. 지난달 보고서·AI 추천·법무 요청은 세지 않는다."""
    old, run_old = new_review(mkt, title="지난달 건")
    finish(agent_http, run_old, old, "SUITABLE")
    add_legal(old, run_old, mkt.user_id)
    new, run_new = new_review(mkt, title="이번 달 건")
    finish(agent_http, run_new, new, "UNSUITABLE")
    suggest(mkt, agent_http, new)
    last_month = utcnow().replace(day=1) - timedelta(days=40)
    with SessionLocal() as db:
        db.execute(update(Report).where(Report.review_id == old).values(created_at=last_month))
        db.execute(update(LegalSubmission).where(LegalSubmission.review_id == old).values(sent_at=last_month))
        db.commit()
    summary = mkt.get(f"{API}/dashboard").json()["summary"]
    assert summary == {"completedReviews": 1, "raReviews": 1, "legalSentReviews": 0}


# ---------- 법무 검토함·대시보드 ----------


def test_legal_list_and_dashboard(mkt, legal, agent_http):
    subs = {}
    for name, status, reviewer, ago in [
        ("대기", "PENDING", None, None),
        ("내 검토 중", "IN_REVIEW", legal.user_id, None),
        ("오늘 전송", "OPINION_SENT", legal.user_id, timedelta(0)),
        ("열흘 전 전송", "OPINION_SENT", legal.user_id, timedelta(days=10)),
    ]:
        rev, run = new_review(mkt, title=name)
        finish(agent_http, run, rev, "SUITABLE")
        subs[name] = add_legal(rev, run, mkt.user_id, status, reviewer, ago)

    rows = items(legal, "/legal-submissions")
    assert [r["submissionId"] for r in rows] == [subs["열흘 전 전송"], subs["오늘 전송"], subs["내 검토 중"], subs["대기"]]
    rows = by_id(rows, "submissionId")
    assert rows[subs["대기"]]["allowedActions"] == ["START_LEGAL_REVIEW"] and rows[subs["대기"]]["reviewer"] is None
    assert rows[subs["내 검토 중"]]["allowedActions"] == ["SEND_OPINION"]
    assert rows[subs["내 검토 중"]]["reviewer"] == {"userId": legal.user_id, "name": "법무A"}
    assert rows[subs["오늘 전송"]]["allowedActions"] == [] and rows[subs["오늘 전송"]]["decision"] == "SUITABLE"

    assert [r["submissionId"] for r in items(legal, "/legal-submissions", status="PENDING")] == [subs["대기"]]
    assert len(items(legal, "/legal-submissions", reviewer="ME")) == 3
    assert [r["submissionId"] for r in items(legal, "/legal-submissions", decidedPeriod="TODAY")] == [subs["오늘 전송"]]
    assert len(items(legal, "/legal-submissions", decidedPeriod="LAST_7_DAYS")) == 1
    assert [r["submissionId"] for r in items(legal, "/legal-submissions", q="대기")] == [subs["대기"]]

    body = legal.get(f"{API}/dashboard").json()
    assert body["role"] == "LEGAL"
    assert body["tasks"] == {"pending": 1, "inReview": 1, "completedToday": 1}
    assert body["summary"]["receivedThisMonth"] == 4
    assert len(body["recentReports"]) == 4 and body["recentReports"][0]["submissionId"] == subs["열흘 전 전송"]
