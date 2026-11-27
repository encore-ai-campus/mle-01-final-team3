"""같은 검토 건에 실행을 만드는 요청이 동시에 와도 실행 중인 건은 하나만 생긴다 (reviews 행 잠금).

다른 세션이 검토 건 행을 잠가 둔 채로 요청 두 개를 보내, 두 요청이 잠금을 기다리는지와
잠금을 푼 뒤 하나만 202, 나머지는 409인지 확인한다.
"""

import threading

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.main import app
from app.models import Review, ReviewRun
from tests.helpers import API, fail, finish, new_review


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
