"""사용자 만들기. CLI(첫 ADMIN), 개발용 시드, 관리자 사용자 등록 API가 함께 쓴다."""

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.core.ids import new_id
from app.core.security import hash_password, utcnow
from app.models import User

ROLES = ("ADMIN", "MARKETING", "LEGAL")


def create_user(
    db: DbSession,
    *,
    name: str,
    email: str,
    role: str,
    password: str,
    must_change_password: bool = True,
) -> User:
    if role not in ROLES:
        raise ValueError(f"알 수 없는 역할: {role}")
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise ApiError(
            409,
            "EMAIL_ALREADY_EXISTS",
            "이미 등록된 이메일입니다.",
            field_errors=[{"field": "email", "code": "DUPLICATE"}],
        )
    user = User(
        id=new_id(db, "usr"),
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        must_change_password=must_change_password,
        created_at=utcnow(),
    )
    db.add(user)
    db.flush()
    return user
