"""5단계: 관리자 계정 발급·로그인·로그아웃·비밀번호 변경 확인."""

from datetime import timedelta

from sqlalchemy import select, update

from app.admin_users.service import create_user
from app.cli import create_admin
from app.core.ids import new_id
from app.models import ActivityLog, Notification, Session, User

PW = "password123"


def make_user(db, email="m@test.com", role="MARKETING", status="ACTIVE", must_change=False):
    user = create_user(db, name="테스트", email=email, role=role, password=PW, must_change_password=must_change)
    user.status = status
    db.commit()
    return user


def login(client, email="m@test.com", password=PW, **extra):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password, **extra})


def assert_error(res, status, code):
    assert res.status_code == status, res.text
    err = res.json()["error"]
    assert err["code"] == code
    assert err["requestId"].startswith("req_")
    assert "message" in err and "retryable" in err and "fieldErrors" in err


# ---------- ID ----------


def test_new_id_is_prefix_and_number(db):
    a, b = new_id(db, "usr"), new_id(db, "usr")
    assert a.startswith("usr_") and b.startswith("usr_")
    assert int(b.split("_")[1]) == int(a.split("_")[1]) + 1


# ---------- 로그인 성공 ----------


def test_login_success_sets_cookie_and_8h_session(client, db):
    user = make_user(db)
    res = login(client)
    assert res.status_code == 200
    assert res.json() == {
        "user": {"userId": user.id, "name": "테스트", "email": "m@test.com", "role": "MARKETING"},
        "mustChangePassword": False,
    }
    cookie = res.headers["set-cookie"]
    assert "adguard_session=" in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()

    db.expire_all()
    session = db.scalar(select(Session).where(Session.user_id == user.id))
    assert session.expires_at - session.created_at == timedelta(hours=8)
    assert db.get(User, user.id).last_login_at is not None
    assert db.scalar(select(ActivityLog.operation).where(ActivityLog.user_id == user.id)) == "LOGIN"


def test_admin_login(client, db):
    make_user(db, email="a@test.com", role="ADMIN")
    assert login(client, email="a@test.com", loginType="ADMIN").status_code == 200


def test_staff_login_type(client, db):
    # 기표님 테스트는 담당자 로그인에 loginType=STAFF를 보낸다
    make_user(db)
    assert login(client, loginType="STAFF").status_code == 200


def test_admin_login_checks_role_before_inactive(client, db):
    # 기표님 샘플과 같은 순서: 관리자 로그인에 비관리자면 비활성 여부보다 ADMIN_ROLE_REQUIRED가 먼저
    make_user(db, status="INACTIVE")
    assert_error(login(client, loginType="ADMIN"), 403, "ADMIN_ROLE_REQUIRED")


# ---------- 로그인 실패 ----------


def test_login_unknown_email(client):
    assert_error(login(client, email="none@test.com"), 401, "USER_NOT_FOUND")


def test_login_deleted_user_is_same_as_unknown(client, db):
    make_user(db, status="DELETED")
    assert_error(login(client), 401, "USER_NOT_FOUND")


def test_login_wrong_password(client, db):
    make_user(db)
    assert_error(login(client, password="wrong1234"), 401, "INVALID_PASSWORD")


def test_login_inactive(client, db):
    make_user(db, status="INACTIVE")
    assert_error(login(client), 403, "ACCOUNT_INACTIVE")


def test_admin_login_with_non_admin(client, db):
    make_user(db)
    assert_error(login(client, loginType="ADMIN"), 403, "ADMIN_ROLE_REQUIRED")


def test_login_missing_field(client):
    res = client.post("/api/v1/auth/login", json={"email": "m@test.com"})
    assert_error(res, 422, "VALIDATION_ERROR")
    assert res.json()["error"]["fieldErrors"] == [{"field": "password", "code": "REQUIRED"}]


# ---------- 세션 ----------


def test_me_requires_login(client):
    assert_error(client.get("/api/v1/me"), 401, "UNAUTHENTICATED")


def test_me_after_login(client, db):
    user = make_user(db)
    login(client)
    res = client.get("/api/v1/me")
    assert res.status_code == 200
    assert res.json()["userId"] == user.id


def test_expired_session_is_401(client, db):
    make_user(db)
    login(client)
    db.execute(update(Session).values(expires_at=Session.created_at))  # 만료시킴
    db.commit()
    assert_error(client.get("/api/v1/me"), 401, "UNAUTHENTICATED")


def test_logout_deletes_session(client, db):
    user = make_user(db)
    login(client)
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert db.scalar(select(Session).where(Session.user_id == user.id)) is None
    assert_error(client.get("/api/v1/me"), 401, "UNAUTHENTICATED")


def test_deactivated_user_session_is_401(client, db):
    user = make_user(db)
    login(client)
    db.execute(update(User).where(User.id == user.id).values(status="INACTIVE"))
    db.commit()
    assert_error(client.get("/api/v1/me"), 401, "UNAUTHENTICATED")


# ---------- 임시 비밀번호·비밀번호 변경 ----------


def _password_notices(db, user_id):
    db.expire_all()
    return db.scalars(
        select(Notification).where(
            Notification.user_id == user_id, Notification.type == "PASSWORD_CHANGE_REQUIRED"
        )
    ).all()


def test_temporary_password_notifies_without_blocking(client, db):
    user = make_user(db, must_change=True)
    res = login(client)
    assert res.json()["mustChangePassword"] is True
    assert client.get("/api/v1/me").status_code == 200  # 막지 않음
    login(client)  # 다시 로그인해도 안 읽은 안내가 있으면 중복으로 만들지 않음
    assert len(_password_notices(db, user.id)) == 1


def test_change_password(client, db):
    user = make_user(db, must_change=True)
    login(client)
    res = client.patch("/api/v1/me/password", json={"currentPassword": PW, "newPassword": "newpass456"})
    assert res.status_code == 200
    assert res.json()["mustChangePassword"] is False
    assert all(n.read_at is not None for n in _password_notices(db, user.id))

    client.post("/api/v1/auth/logout")
    assert login(client, password="newpass456").status_code == 200
    assert_error(login(client, password=PW), 401, "INVALID_PASSWORD")


def test_change_password_wrong_current(client, db):
    make_user(db)
    login(client)
    res = client.patch("/api/v1/me/password", json={"currentPassword": "wrong1234", "newPassword": "newpass456"})
    assert_error(res, 422, "INVALID_CURRENT_PASSWORD")


def test_change_password_policy(client, db):
    make_user(db)
    login(client)
    for weak in ["short1", "onlyletters", "12345678"]:
        res = client.patch("/api/v1/me/password", json={"currentPassword": PW, "newPassword": weak})
        assert_error(res, 422, "PASSWORD_POLICY_VIOLATION")


# ---------- 첫 ADMIN (CLI) ----------


def test_cli_create_admin_then_login(client, db):
    user_id, temp = create_admin("first@test.com", "첫 관리자")
    user = db.get(User, user_id)
    assert user.role == "ADMIN" and user.must_change_password is True
    res = login(client, email="first@test.com", password=temp, loginType="ADMIN")
    assert res.status_code == 200
    assert res.json()["mustChangePassword"] is True


def test_duplicate_email(db):
    make_user(db)
    try:
        create_user(db, name="x", email="m@test.com", role="LEGAL", password=PW)
    except Exception as e:
        assert getattr(e, "code", None) == "EMAIL_ALREADY_EXISTS"
    else:
        raise AssertionError("중복 이메일이 통과됨")
