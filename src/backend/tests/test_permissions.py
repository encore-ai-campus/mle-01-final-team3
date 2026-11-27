"""6단계: 역할별 접근 제어, 세션 강제 종료, Agent 서비스 인증 확인.

실제 업무 API가 아직 없으므로 테스트 전용 앱에 권한별 API를 하나씩 붙여서 확인한다.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.admin_users.service import create_user
from app.auth.router import router as auth_router
from app.auth.sessions import revoke_user_sessions
from app.core.config import settings
from app.core.deps import Admin, CurrentUser, Lawyer, Marketer, Staff, verify_agent_token
from app.core.errors import register_error_handlers

PW = "password123"

probe = FastAPI()
register_error_handlers(probe)
probe.include_router(auth_router, prefix="/api/v1")


@probe.get("/probe/any")
def any_user(user: CurrentUser):
    return {"ok": True}


@probe.get("/probe/marketing")
def marketing_only(user: Marketer):
    return {"ok": True}


@probe.get("/probe/legal")
def legal_only(user: Lawyer):
    return {"ok": True}


@probe.get("/probe/admin")
def admin_only(user: Admin):
    return {"ok": True}


@probe.get("/probe/staff")
def staff_only(user: Staff):
    return {"ok": True}


@probe.post("/probe/agent", dependencies=[Depends(verify_agent_token)])
def agent_only():
    return {"ok": True}


# 권한 매트릭스: (주소, {역할: 기대 상태 코드})
MATRIX = [
    ("/probe/any", {"ADMIN": 200, "MARKETING": 200, "LEGAL": 200}),
    ("/probe/marketing", {"ADMIN": 403, "MARKETING": 200, "LEGAL": 403}),
    ("/probe/legal", {"ADMIN": 403, "MARKETING": 403, "LEGAL": 200}),
    ("/probe/admin", {"ADMIN": 200, "MARKETING": 403, "LEGAL": 403}),
    ("/probe/staff", {"ADMIN": 403, "MARKETING": 200, "LEGAL": 200}),
]


def logged_in(db, role: str) -> TestClient:
    email = f"{role.lower()}@test.com"
    create_user(db, name=role, email=email, role=role, password=PW, must_change_password=False)
    db.commit()
    c = TestClient(probe)
    login_type = "ADMIN" if role == "ADMIN" else "STAFF"
    assert c.post("/api/v1/auth/login", json={"email": email, "password": PW, "loginType": login_type}).status_code == 200
    return c


@pytest.mark.parametrize("role", ["ADMIN", "MARKETING", "LEGAL"])
def test_role_matrix(db, role):
    c = logged_in(db, role)
    for path, expected in MATRIX:
        res = c.get(path)
        assert res.status_code == expected[role], f"{role} {path} → {res.status_code}"
        if res.status_code == 403:
            assert res.json()["error"]["code"] == "FORBIDDEN"


def test_not_logged_in_is_401_everywhere():
    c = TestClient(probe)
    for path, _ in MATRIX:
        res = c.get(path)
        assert res.status_code == 401 and res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_revoke_user_sessions_logs_out_all_devices(db):
    pc, phone = logged_in(db, "MARKETING"), TestClient(probe)
    phone.post("/api/v1/auth/login", json={"email": "marketing@test.com", "password": PW})
    user_id = pc.get("/api/v1/me").json()["userId"]

    assert revoke_user_sessions(db, user_id) == 2
    db.commit()
    assert pc.get("/probe/any").status_code == 401
    assert phone.get("/probe/any").status_code == 401


def test_role_change_takes_effect_after_relogin(db):
    """역할을 바꾸면 세션을 지우므로, 다시 로그인한 뒤 새 역할 권한이 적용된다."""
    from app.models import User

    c = logged_in(db, "MARKETING")
    user = db.query(User).filter_by(email="marketing@test.com").one()
    user.role = "LEGAL"
    revoke_user_sessions(db, user.id)
    db.commit()
    assert c.get("/probe/marketing").status_code == 401
    c.post("/api/v1/auth/login", json={"email": "marketing@test.com", "password": PW})
    assert c.get("/probe/marketing").status_code == 403
    assert c.get("/probe/legal").status_code == 200


def test_agent_token(monkeypatch):
    c = TestClient(probe)
    monkeypatch.setattr(settings, "agent_token", "")
    assert c.post("/probe/agent", headers={"Authorization": "Bearer "}).status_code == 401  # 설정 안 하면 모두 거절

    monkeypatch.setattr(settings, "agent_token", "secret-1")
    assert c.post("/probe/agent").status_code == 401
    assert c.post("/probe/agent", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert c.post("/probe/agent", headers={"Authorization": "Bearer secret-1"}).status_code == 200
