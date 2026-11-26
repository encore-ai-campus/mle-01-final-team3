"""로그인·로그아웃·내 정보·비밀번호 변경. API 설계서 4·5장."""

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session as DbSession

from app.core.activity import log_activity
from app.core.config import settings
from app.core.deps import SESSION_COOKIE, Auth, get_auth, get_current_user, get_db
from app.core.errors import ApiError
from app.core.schemas import CamelModel
from app.core.security import (
    hash_password,
    hash_token,
    is_valid_password,
    new_session_token,
    utcnow,
    verify_password,
)
from app.models import Notification, Session, User
from app.notifications.service import notify

router = APIRouter()

# 문구는 기표님 샘플(backend-test v5.2)과 같게 맞춘다.
PASSWORD_NOTICE = "처음 로그인하셨습니다. 현재 비밀번호는 임시 비밀번호이니 마이페이지에서 새 비밀번호로 변경 바랍니다."


class LoginRequest(CamelModel):
    email: str
    password: str
    login_type: Literal["STAFF", "ADMIN"] = "STAFF"  # 담당자 로그인 STAFF, 관리자 로그인 ADMIN


class PasswordChangeRequest(CamelModel):
    current_password: str
    new_password: str


def user_body(user: User) -> dict:
    return {"userId": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.post("/auth/login")
def login(body: LoginRequest, response: Response, db: DbSession = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email))
    # '삭제된 사용자'는 없는 계정과 같이 처리한다.
    if user is None or user.status == "DELETED":
        raise ApiError(401, "USER_NOT_FOUND", "등록되지 않은 아이디입니다.")
    if not verify_password(body.password, user.password_hash):
        raise ApiError(401, "INVALID_PASSWORD", "비밀번호가 올바르지 않습니다.")
    if body.login_type == "ADMIN" and user.role != "ADMIN":
        raise ApiError(403, "ADMIN_ROLE_REQUIRED", "관리자 권한이 없는 계정입니다. 담당자 로그인을 이용해 주세요.")
    if user.status != "ACTIVE":
        who = "다른 관리자" if body.login_type == "ADMIN" else "관리자"
        raise ApiError(403, "ACCOUNT_INACTIVE", f"비활성화된 계정입니다. {who}에게 문의해 주세요.")

    now = utcnow()
    token = new_session_token()
    # 이 사용자의 만료된 세션은 로그인할 때 정리한다.
    db.execute(delete(Session).where(Session.user_id == user.id, Session.expires_at <= now))
    db.add(
        Session(
            token_hash=hash_token(token),
            user_id=user.id,
            created_at=now,
            expires_at=now + timedelta(hours=settings.session_hours),  # 고정 10시간
        )
    )
    user.last_login_at = now
    log_activity(db, user.id, "LOGIN")

    # 임시 비밀번호 상태면 막지 않고 알림으로 안내한다. 안 읽은 안내가 이미 있으면 또 만들지 않는다.
    if user.must_change_password and not _has_unread_password_notice(db, user.id):
        notify(db, user.id, "PASSWORD_CHANGE_REQUIRED", PASSWORD_NOTICE)

    db.commit()

    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return {"user": user_body(user), "mustChangePassword": bool(user.must_change_password)}


@router.post("/auth/logout", status_code=204)
def logout(response: Response, auth: Auth = Depends(get_auth), db: DbSession = Depends(get_db)) -> None:
    db.execute(delete(Session).where(Session.token_hash == auth.session.token_hash))
    log_activity(db, auth.user.id, "LOGOUT")
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {**user_body(user), "mustChangePassword": bool(user.must_change_password)}


@router.patch("/me/password")
def change_password(
    body: PasswordChangeRequest,
    auth: Auth = Depends(get_auth),
    db: DbSession = Depends(get_db),
) -> dict:
    user = db.get(User, auth.user.id)
    if not verify_password(body.current_password, user.password_hash):
        raise ApiError(
            422,
            "INVALID_CURRENT_PASSWORD",
            "현재 비밀번호가 올바르지 않습니다.",
            field_errors=[{"field": "currentPassword", "code": "INVALID"}],
        )
    if not is_valid_password(body.new_password):
        raise ApiError(
            422,
            "PASSWORD_POLICY_VIOLATION",
            "8자 이상, 영문·숫자를 포함해 주세요.",
            field_errors=[{"field": "newPassword", "code": "INVALID"}],
        )
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    # 비밀번호를 바꾸면 '비밀번호 변경' 안내 알림은 읽음 처리한다.
    db.execute(
        update(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.type == "PASSWORD_CHANGE_REQUIRED",
            Notification.read_at.is_(None),
        )
        .values(read_at=utcnow())
    )
    db.commit()
    return {**user_body(user), "mustChangePassword": False}


def _has_unread_password_notice(db: DbSession, user_id: str) -> bool:
    return (
        db.scalar(
            select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.type == "PASSWORD_CHANGE_REQUIRED",
                Notification.read_at.is_(None),
            )
        )
        is not None
    )
