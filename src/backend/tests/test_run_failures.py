"""실패·시간 초과·재시도·Agent 연결 불가·중복·지연 완료 통지."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from app.core.db import SessionLocal
from app.models import Report, ReviewRun
from app.reviews.runs import expire_overdue_runs
from tests.helpers import (
    API,
    DOWNLOAD_ERROR,
    INPUT_ERROR,
    SUGGESTION,
    TEMP_ERROR,
    complete,
    detail,
    fail,
    finish,
    new_review,
    report,
    run_of,
    suggest,
)


def age_run(run_id: str, seconds: int = 181) -> None:
    """실행을 만든 시각을 과거로 돌려 시간 초과를 흉내 낸다."""
    with SessionLocal() as db:
        db.execute(
            update(ReviewRun).where(ReviewRun.id == run_id).values(created_at=ReviewRun.created_at - timedelta(seconds=seconds))
        )
        db.commit()


# ---------- 실패 ----------


@pytest.mark.parametrize("error", [TEMP_ERROR, DOWNLOAD_ERROR], ids=["search", "attachment_download"])
def test_failed_retryable_shows_retry(mkt, agent_http, error):
    rev, run = new_review(mkt)
    res = fail(agent_http, run, rev, error)
    assert res["runStatus"] == "FAILED" and res["error"] == error and res["finishedAt"]
    d = detail(mkt, rev)
    assert d["runStatus"] == "FAILED" and d["report"] is None and d["latestRunId"] == run
    assert d["allowedActions"] == ["RETRY_RUN"]


def test_failed_not_retryable_only_cancel(mkt, agent_http):
    rev, run = new_review(mkt)
    fail(agent_http, run, rev, INPUT_ERROR)
    assert detail(mkt, rev)["allowedActions"] == ["CANCEL"]
    r = mkt.post(f"{API}/review-runs/{run}/retry")
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"


def test_suggest_failure_keeps_report(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    ra = mkt.post(f"{API}/reviews/{rev}/ra-runs").json()["runId"]
    fail(agent_http, ra, rev, TEMP_ERROR)
    d = detail(mkt, rev)
    assert d["report"]["runId"] == run and d["report"]["version"] == 1 and d["latestRunId"] == ra
    assert d["allowedActions"] == ["RETRY_RUN", "CANCEL"]


# ---------- 재시도 ----------


def test_retry_creates_new_run(mkt, agent, agent_http):
    rev, run = new_review(mkt)
    fail(agent_http, run, rev)
    r = mkt.post(f"{API}/review-runs/{run}/retry")
    assert r.status_code == 202 and r.headers["Location"].endswith(r.json()["runId"])
    new = r.json()["runId"]
    assert new != run and r.json()["stage"] == "AI_SCREENING"
    assert run_of(mkt, new)["attempt"] == 2
    assert run_of(mkt, run)["runStatus"] == "FAILED"  # 실패한 실행은 그대로 남김
    assert agent.last()["runId"] == new
    finish(agent_http, new, rev)
    assert detail(mkt, rev)["report"]["version"] == 1


def test_retry_limit_is_two(mkt, agent_http):
    rev, run = new_review(mkt)
    for _ in range(2):
        fail(agent_http, run, rev)
        run = mkt.post(f"{API}/review-runs/{run}/retry").json()["runId"]
    assert run_of(mkt, run)["attempt"] == 3
    fail(agent_http, run, rev)
    r = mkt.post(f"{API}/review-runs/{run}/retry")
    assert r.status_code == 409 and r.json()["error"]["code"] == "RETRY_LIMIT_REACHED"


def test_retry_only_latest_failed_run(mkt, agent_http):
    rev, run = new_review(mkt)
    assert mkt.post(f"{API}/review-runs/{run}/retry").status_code == 409  # 실행 중
    fail(agent_http, run, rev)
    new = mkt.post(f"{API}/review-runs/{run}/retry").json()["runId"]
    fail(agent_http, new, rev)
    r = mkt.post(f"{API}/review-runs/{run}/retry")  # 예전 실패 실행
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"


def test_retry_by_other_user_403(mkt, mkt_b, agent_http):
    rev, run = new_review(mkt)
    fail(agent_http, run, rev)
    assert mkt_b.post(f"{API}/review-runs/{run}/retry").status_code == 403


def test_recheck_retry_uses_same_suggestion_text(mkt, agent, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    recheck = mkt.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/recheck").json()["runId"]
    fail(agent_http, recheck, rev)
    assert detail(mkt, rev)["allowedActions"] == ["RETRY_RUN", "CANCEL"]

    retry = mkt.post(f"{API}/review-runs/{recheck}/retry").json()
    assert retry["stage"] == "RA_RECHECK"
    assert agent.last()["runId"] == retry["runId"] and agent.last()["text"] == SUGGESTION["text"]

    rep = report("SUITABLE")
    assert complete(agent_http, retry["runId"], rev, report=rep).status_code == 200
    d = detail(mkt, rev)
    assert d["report"]["version"] == 2 and d["report"]["reviewedText"] == SUGGESTION["text"]


# ---------- Agent 연결 불가 ----------


def test_agent_unavailable_after_three_sends(mkt, agent):
    agent.down = True
    rev, run = new_review(mkt)
    assert agent.sends_for(run) == 3  # 같은 runId로 3번
    res = run_of(mkt, run)
    assert res["runStatus"] == "FAILED" and res["startedAt"] is None
    assert res["error"]["code"] == "AGENT_UNAVAILABLE" and res["error"]["retryable"] is True
    assert detail(mkt, rev)["allowedActions"] == ["RETRY_RUN"]

    agent.down = False
    new = mkt.post(f"{API}/review-runs/{run}/retry").json()["runId"]
    assert run_of(mkt, new)["runStatus"] == "RUNNING"


# ---------- 시간 초과 ----------


def test_timeout_after_180s(mkt, agent_http):
    rev, run = new_review(mkt)
    age_run(run, 179)
    assert run_of(mkt, run)["runStatus"] == "RUNNING"
    age_run(run, 2)
    res = run_of(mkt, run)
    assert res["runStatus"] == "FAILED"
    assert res["error"] == {"code": "RUN_TIMEOUT", "message": "검토 시간이 초과되었습니다. 다시 검토해 주세요.", "retryable": True}
    assert detail(mkt, rev)["allowedActions"] == ["RETRY_RUN"]


def test_expire_overdue_runs_for_lists(mkt):
    """목록·대시보드용: 180초가 지난 실행만 한꺼번에 RUN_TIMEOUT."""
    rev_old, old = new_review(mkt, title="오래된 검토")
    rev_new, new = new_review(mkt, title="새 검토")
    age_run(old, 181)
    age_run(new, 179)
    with SessionLocal() as db:
        assert expire_overdue_runs(db, [rev_new]) == 0  # 범위를 주면 그 검토 건만
        assert expire_overdue_runs(db) == 1
        db.commit()
    with SessionLocal() as db:
        old_run, new_run = db.get(ReviewRun, old), db.get(ReviewRun, new)
        assert (old_run.status, old_run.error_code) == ("FAILED", "RUN_TIMEOUT")
        assert new_run.status == "RUNNING"


def test_timeout_seen_from_detail_too(mkt):
    rev, run = new_review(mkt)
    age_run(run)
    d = detail(mkt, rev)
    assert d["runStatus"] == "FAILED" and d["allowedActions"] == ["RETRY_RUN"]


def test_late_success_after_timeout_is_409(mkt, agent_http):
    rev, run = new_review(mkt)
    age_run(run)
    r = complete(agent_http, run, rev, report=report())
    assert r.status_code == 409 and r.json()["error"]["code"] == "STATE_CONFLICT"
    assert run_of(mkt, run)["error"]["code"] == "RUN_TIMEOUT"  # 덮어쓰지 않음
    with SessionLocal() as db:
        assert db.scalars(select(Report).where(Report.review_id == rev)).first() is None


def test_late_failure_after_timeout_is_ignored(mkt, agent_http):
    rev, run = new_review(mkt)
    age_run(run)
    r = complete(agent_http, run, rev, "FAILED", error=TEMP_ERROR)
    assert r.status_code == 200 and r.json()["error"]["code"] == "RUN_TIMEOUT"


# ---------- 중복 완료 통지 ----------


def test_duplicate_success_processed_once(mkt, agent_http):
    rev, run = new_review(mkt)
    first = finish(agent_http, run, rev)
    second = complete(agent_http, run, rev, report=report("SUITABLE"))  # 같은 runStatus 재전송
    assert second.status_code == 200 and second.json()["finishedAt"] == first["finishedAt"]
    d = detail(mkt, rev)
    assert d["report"]["decision"] == "UNSUITABLE" and d["report"]["version"] == 1  # 처음 결과 유지


def test_different_status_after_done_is_409(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    r = complete(agent_http, run, rev, "FAILED", error=TEMP_ERROR)
    assert r.status_code == 409


def test_duplicate_suggestion_keeps_pending(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    again = complete(agent_http, sug_run, rev, suggestion={"text": "다른 문구", "rationale": "다른 이유"})
    assert again.status_code == 200
    assert detail(mkt, rev)["suggestion"]["text"] == SUGGESTION["text"]


def test_completion_before_running_is_accepted(mkt, agent, agent_http):
    """Agent가 202보다 완료 통지를 먼저 보내도 처리한다 (QUEUED → SUCCEEDED)."""
    agent.down = True
    rev, run = new_review(mkt)  # 3번 실패 → AGENT_UNAVAILABLE이 되기 전 상황을 직접 만든다
    with SessionLocal() as db:
        db.execute(update(ReviewRun).where(ReviewRun.id == run).values(status="QUEUED", error_code=None,
                                                                        error_message=None, error_retryable=None,
                                                                        finished_at=None))  # fmt: skip
        db.commit()
    res = finish(agent_http, run, rev)
    assert res["runStatus"] == "SUCCEEDED" and res["startedAt"]
