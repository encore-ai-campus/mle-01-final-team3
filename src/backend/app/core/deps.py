"""API에서 공통으로 쓰는 의존성: DB 세션, 로그인 사용자 확인, 역할별 접근 제어, Agent 서비스 인증.

사용 예 (검토 흐름·AI 연동 담당 샘플과 같은 이름):

    @router.post("/reviews")
    def create_review(user: Marketer, db: DbSession = Depends(get_db)): ...

- CurrentUser: 로그인만 하면 누구나
- Marketer / Lawyer / Admin: 그 역할만
- Staff: 마케팅·법무 (관리자 제외)
"""

import hmac
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.errors import ApiError
from app.core.security import hash_token, utcnow
from app.models import Session, User

SESSION_COOKIE = "adguard_session"


def get_db() -> Iterator[DbSession]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass
class Auth:
    user: User
    session: Session


def get_auth(request: Request, db: DbSession = Depends(get_db)) -> Auth:
    """쿠키의 세션 토큰으로 로그인 사용자를 찾는다. 없거나 만료되면 401 UNAUTHENTICATED."""
    token = request.cookies.get(SESSION_COOKIE)
    session = db.get(Session, hash_token(token)) if token else None
    if session is None or session.expires_at <= utcnow():
        raise ApiError(401, "UNAUTHENTICATED", "로그인이 필요합니다.")
    user = db.get(User, session.user_id)
    if user is None or user.status != "ACTIVE":
        raise ApiError(401, "UNAUTHENTICATED", "로그인이 필요합니다.")
    return Auth(user=user, session=session)


def get_current_user(auth: Auth = Depends(get_auth)) -> User:
    return auth.user


def require_roles(*roles: str) -> Callable[[User], User]:
    """허용한 역할이 아니면 403 FORBIDDEN."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ApiError(403, "FORBIDDEN", "이 화면을 사용할 권한이 없습니다.")
        return user

    return checker


CurrentUser = Annotated[User, Depends(get_current_user)]
Marketer = Annotated[User, Depends(require_roles("MARKETING"))]
Lawyer = Annotated[User, Depends(require_roles("LEGAL"))]
Admin = Annotated[User, Depends(require_roles("ADMIN"))]
Staff = Annotated[User, Depends(require_roles("MARKETING", "LEGAL"))]


def verify_agent_token(authorization: Annotated[str | None, Header()] = None) -> None:
    """Agent → 백엔드 완료 통지용 서비스 인증. 헤더 `Authorization: Bearer {AGENT_TOKEN}`.

    AGENT_TOKEN이 설정되지 않았으면 모든 요청을 거절한다.
    """
    expected = f"Bearer {settings.agent_token}" if settings.agent_token else None
    if expected is None or not hmac.compare_digest(authorization or "", expected):
        raise ApiError(401, "UNAUTHENTICATED", "서비스 인증에 실패했습니다.")
