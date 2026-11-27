"""검토 건 행 잠금과 잠금 순서 (설계서 3장: users → reviews → review_runs).

1. 같은 검토 건에 실행을 만드는 요청이 동시에 와도 실행 중인 건은 하나만 생긴다.
   다른 세션이 검토 건 행을 잠가 둔 채로 요청 두 개를 보내, 두 요청이 잠금을 기다리는지와
   잠금을 푼 뒤 하나만 202, 나머지는 409인지 확인한다.
2. 실행·법무 요청을 바꾸는 처리(완료 통지·시간 초과·Agent 작업 요청 결과·재심의/닫기·[검토 시작]·의견 전송)는
   실행·법무 요청 행보다 검토 건 행을 먼저 잠근다.
   다른 세션이 검토 건을 잠근 동안 그 처리가 검토 건 잠금을 기다리고, 실행 행은 아직 잡지 않았는지(NOWAIT로 잠가 봄) 확인한다.
   순서가 반대면 실행 행을 잡은 채 검토 건을 기다려, 검토 건을 잡고 실행을 기다리는 요청과 교착이 생긴다.
"""

import threading
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import OperationalError

from app.agent.dispatch import dispatch_run
from app.core.db import SessionLocal
from app.main import app
from app.models import LegalSubmission, Review, ReviewRun
from app.reviews import codes as C
from app.reviews.runs import expire_overdue_runs
from tests.helpers import API, complete, fail, finish, new_review, report, run_of, suggest


def _client_like(c: TestClient) -> TestClient:
    """같은 로그인 세션을 쓰는 별도 클라이언트 (스레드마다 하나)."""
    other = TestClient(app)
    other.cookies.set("adguard_session", c.cookies.get("adguard_session"))
    return other


def _send_while_review_locked(review_id: str, send) -> list[int]:
    """검토 건 행을 잠근 채 요청 두 개를 보내고, 둘 다 기다리는지 확인한 뒤 잠금을 푼다. 응답 코드 두 개를 돌려준다."""
    results: list[int] = []
    holder = SessionLocal()
    try:
        holder.execute(select(Review).where(Review.id == review_id).with_for_update())
        threads = [threading.Thread(target=lambda: results.append(send())) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(0.5)
        assert all(t.is_alive() for t in threads), "검토 건 잠금을 기다리지 않았다"
    finally:
        holder.rollback()
        holder.close()
    for t in threads:
        t.join(10)
    return sorted(results)


def _count_runs(review_id: str, **filters) -> int:
    with SessionLocal() as db:
        q = select(func.count()).select_from(ReviewRun).where(ReviewRun.review_id == review_id)
        for k, v in filters.items():
            q = q.where(getattr(ReviewRun, k) == v)
        return db.scalar(q)


def test_two_ai_suggestion_requests_at_once_make_one_run(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "UNSUITABLE")
    clients = [_client_like(mkt), _client_like(mkt)]

    codes = _send_while_review_locked(rev, lambda: clients.pop().post(f"{API}/reviews/{rev}/ra-runs").status_code)

    assert codes == [202, 409]
    assert _count_runs(rev, stage="RA_SUGGEST") == 1


def test_two_retries_at_once_make_one_run(mkt, agent_http):
    rev, run = new_review(mkt)
    fail(agent_http, run, rev)
    clients = [_client_like(mkt), _client_like(mkt)]

    codes = _send_while_review_locked(rev, lambda: clients.pop().post(f"{API}/review-runs/{run}/retry").status_code)

    assert codes == [202, 409]
    assert _count_runs(rev, retry_of=run) == 1


# ---------- 잠금 순서: 검토 건 → 실행 ----------


def _run_lock_is_free(run_id: str) -> bool:
    """다른 세션에서 실행 행을 NOWAIT로 잠가 본다. 바로 잠기면 아무도 그 실행 행을 잡고 있지 않다."""
    probe = SessionLocal()
    try:
        probe.execute(select(ReviewRun.id).where(ReviewRun.id == run_id).with_for_update(nowait=True))
        return True
    except OperationalError:
        return False
    finally:
        probe.rollback()
        probe.close()


def _check_order(review_id: str, row_id: str, action, probe=None):
    """검토 건 행을 잠근 채 action을 스레드로 돌린다. (검토 건 잠금을 기다렸는지, 그동안 뒤에 잠글 행이 비어 있었는지, action 결과)

    probe: 뒤에 잠글 행이 비어 있는지 보는 함수. 기본은 실행 행.
    """
    result: dict = {}
    holder = SessionLocal()
    try:
        holder.execute(select(Review.id).where(Review.id == review_id).with_for_update())
        t = threading.Thread(target=lambda: result.setdefault("value", action()))
        t.start()
        t.join(0.5)
        waiting = t.is_alive()
        run_free = (probe or _run_lock_is_free)(row_id)
    finally:
        holder.rollback()
        holder.close()
    t.join(10)
    assert not t.is_alive(), "잠금을 푼 뒤에도 끝나지 않았다"
    return waiting, run_free, result.get("value")


def _age(run_id: str, seconds: int = 181) -> None:
    with SessionLocal() as db:
        db.execute(
            update(ReviewRun)
            .where(ReviewRun.id == run_id)
            .values(created_at=ReviewRun.created_at - timedelta(seconds=seconds))
        )
        db.commit()


def test_completion_locks_review_before_run(mkt, agent_http):
    rev, run = new_review(mkt)
    waiting, run_free, code = _check_order(rev, run, lambda: complete(agent_http, run, rev, report=report()).status_code)
    assert waiting and run_free and code == 200


def test_timeout_on_read_locks_review_before_run(mkt):
    rev, run = new_review(mkt)
    _age(run)
    client = _client_like(mkt)
    waiting, run_free, code = _check_order(rev, run, lambda: client.get(f"{API}/review-runs/{run}").status_code)
    assert waiting and run_free and code == 200
    assert run_of(mkt, run)["error"]["code"] == "RUN_TIMEOUT"


def test_dispatch_failure_locks_review_before_run(mkt, agent):
    rev, run = new_review(mkt)
    with SessionLocal() as db:  # Agent가 아직 접수하지 않은 실행으로 되돌린다
        db.execute(update(ReviewRun).where(ReviewRun.id == run).values(status=C.QUEUED, started_at=None))
        db.commit()
    agent.down = True
    waiting, run_free, _ = _check_order(rev, run, lambda: dispatch_run(run))
    assert waiting and run_free
    assert run_of(mkt, run)["error"]["code"] == "AGENT_UNAVAILABLE"


def test_dismiss_locks_review_before_suggestion_run(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    sug_run = suggest(mkt, agent_http, rev)
    client = _client_like(mkt)
    waiting, run_free, code = _check_order(
        rev, sug_run, lambda: client.post(f"{API}/reviews/{rev}/ra-runs/{sug_run}/dismiss").status_code
    )
    assert waiting and run_free and code == 200


def test_list_expiry_skips_locked_review(mkt):
    """목록용 시간 초과 확정은 잠긴 검토 건을 기다리지 않고 건너뛴다. 잠금이 풀리면 확정한다."""
    rev, run = new_review(mkt)
    _age(run)

    def expire() -> int:
        with SessionLocal() as db:
            n = expire_overdue_runs(db)
            db.commit()
            return n

    waiting, run_free, n = _check_order(rev, run, expire)
    assert not waiting and run_free and n == 0
    assert expire() == 1


# ---------- 잠금 순서: 검토 건 → 법무 요청 ----------


def _submission_lock_is_free(submission_id: str) -> bool:
    probe = SessionLocal()
    try:
        probe.execute(
            select(LegalSubmission.id).where(LegalSubmission.id == submission_id).with_for_update(nowait=True)
        )
        return True
    except OperationalError:
        return False
    finally:
        probe.rollback()
        probe.close()


def _sent_to_legal(mkt, agent_http) -> tuple[str, str]:
    """적합 보고서로 법무 검토를 요청한 검토 건. (reviewId, submissionId)"""
    rev, run = new_review(mkt)
    finish(agent_http, run, rev, "SUITABLE")
    r = mkt.post(f"{API}/reviews/{rev}/legal-submissions", json={"reportRunId": run})
    assert r.status_code == 201, r.text
    return rev, r.json()["submissionId"]


def test_legal_start_locks_review_before_submission(mkt, legal, agent_http):
    rev, sub = _sent_to_legal(mkt, agent_http)
    client = _client_like(legal)
    waiting, sub_free, code = _check_order(
        rev, sub, lambda: client.post(f"{API}/legal-submissions/{sub}/start").status_code, _submission_lock_is_free
    )
    assert waiting and sub_free and code == 200


def test_legal_opinion_locks_review_before_submission(mkt, legal, agent_http):
    rev, sub = _sent_to_legal(mkt, agent_http)
    assert legal.post(f"{API}/legal-submissions/{sub}/start").status_code == 200
    client = _client_like(legal)
    send = lambda: client.post(f"{API}/legal-submissions/{sub}/opinion", json={"reason": "근거 자료가 필요합니다."}).status_code  # noqa: E731
    waiting, sub_free, code = _check_order(rev, sub, send, _submission_lock_is_free)
    assert waiting and sub_free and code == 200
