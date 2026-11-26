"""세션 강제 종료. 비활성화·역할 변경·삭제 때 그 사용자의 세션을 모두 지워 바로 로그아웃시킨다."""

from sqlalchemy import delete
from sqlalchemy.orm import Session as DbSession

from app.models import Session


def revoke_user_sessions(db: DbSession, user_id: str) -> int:
    """지운 세션 수를 돌려준다. commit은 부르는 쪽에서 한다 (같은 트랜잭션으로 묶기 위해)."""
    result = db.execute(delete(Session).where(Session.user_id == user_id))
    return result.rowcount or 0
