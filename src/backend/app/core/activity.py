"""활동 로그 기록 (activity_logs). 기표님 쪽 API에서도 이 함수로 남긴다."""

from sqlalchemy.orm import Session as DbSession

from app.core.ids import new_id
from app.core.security import utcnow
from app.models import ActivityLog


def log_activity(db: DbSession, user_id: str, operation: str, target_label: str | None = None) -> None:
    db.add(
        ActivityLog(
            id=new_id(db, "log"),
            user_id=user_id,
            operation=operation,
            target_label=target_label,
            occurred_at=utcnow(),
        )
    )
