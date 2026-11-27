"""사용자 만들기. CLI(첫 ADMIN), 개발용 시드, 관리자 사용자 등록 API가 함께 쓴다."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.core.ids import new_id
from app.core.security import hash_password, utcnow
from app.models import User

ROLES = ("ADMIN", "MARKETING", "LEGAL")


def _duplicate_email() -> ApiError:
    return ApiError(
        409,
        "EMAIL_ALREADY_EXISTS",
        "이미 등록된 이메일입니다.",
        field_errors=[{"field": "email", "code": "DUPLICATE"}],
    )


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
        raise _duplicate_email()
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
    # 두 요청이 동시에 위 확인을 통과해도 DB의 이메일 UNIQUE 규칙이 한쪽을 막는다.
    # 그 오류를 500이 아니라 409로 돌려준다. (savepoint: 실패해도 이 저장만 취소)
    try:
        with db.begin_nested():
            db.add(user)
            db.flush()
    except IntegrityError:
        raise _duplicate_email() from None
    return user
