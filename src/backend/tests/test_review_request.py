"""검토 접수 POST /api/v1/reviews: 로그인·계정 상태, 제품 분류, 트랜잭션 롤백.

정상 접수·첨부 포함·역할 권한·빈 값·멱등성은 test_review_flow.py와 test_attachments.py에 있다.
"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.core.db import SessionLocal
from app.main import app
from app.models import ActivityLog, IdempotencyKey, Review, ReviewAttachment, ReviewRun, User
from app.reviews import router as reviews_router
from tests.helpers import API

BODY = {"title": "면역력 강화 음료 광고", "productCategory": "GENERAL_FOOD", "text": "하루 한 포로 면역력 개선"}


def _count(model) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(model))


def test_not_logged_in_is_401(agent):
    r = TestClient(app).post(f"{API}/reviews", json=BODY)
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"
    assert _count(Review) == 0 and agent.jobs == []


def test_inactive_account_is_401(mkt, agent):
    # 세션이 남아 있어도 계정이 ACTIVE가 아니면 거절한다
    with SessionLocal() as db:
        db.execute(update(User).where(User.id == mkt.user_id).values(status="INACTIVE"))
        db.commit()
    r = mkt.post(f"{API}/reviews", json=BODY)
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"
    assert _count(Review) == 0 and agent.jobs == []


def test_unknown_product_category_is_422(mkt):
    r = mkt.post(f"{API}/reviews", json={**BODY, "productCategory": "DRUG"})
    assert r.status_code == 422
    assert r.json()["error"]["fieldErrors"] == [{"field": "productCategory", "code": "INVALID"}]
    assert _count(Review) == 0


def test_error_while_saving_rolls_back_everything(mkt, agent, monkeypatch):
    """검토 건·첨부 연결·실행을 만든 뒤 활동 로그에서 오류가 나면 아무것도 남지 않는다."""
    att = mkt.post(
        f"{API}/attachments", files={"file": ("근거자료.pdf", b"%PDF-1.4 test")}, data={"purpose": "AD_COPY"}
    ).json()["attachmentId"]
    body = {**BODY, "attachmentIds": [att]}
    headers = {"Idempotency-Key": "rollback-test-key"}

    def broken_log(*args, **kwargs):
        raise RuntimeError("활동 로그 저장 실패 (테스트)")

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("adguard_session", mkt.cookies.get("adguard_session"))
    with monkeypatch.context() as m:  # 이 블록 안에서만 활동 로그 저장이 실패한다
        m.setattr(reviews_router, "log_activity", broken_log)
        r = client.post(f"{API}/reviews", json=body, headers=headers)

    assert r.status_code == 500 and r.json()["error"]["code"] == "INTERNAL_ERROR"
    for model in (Review, ReviewAttachment, ReviewRun, ActivityLog, IdempotencyKey):
        assert _count(model) == 0, model.__tablename__
    assert agent.jobs == []  # 롤백된 실행은 Agent에 보내지 않는다

    # 롤백됐으므로 같은 첨부·같은 Idempotency-Key로 다시 보내면 정상 접수된다
    r = mkt.post(f"{API}/reviews", json=body, headers=headers)
    assert r.status_code == 202
    assert _count(Review) == 1 and _count(ReviewAttachment) == 1 and _count(ReviewRun) == 1
    assert agent.last()["attachments"][0]["attachmentId"] == att
