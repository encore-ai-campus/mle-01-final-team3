"""알림 만들기. 기표님 쪽(AI 추천 완료 등)도 이 함수로 알림을 만든다."""

from sqlalchemy.orm import Session as DbSession

from app.core.ids import new_id
from app.core.security import utcnow
from app.models import Notification


def notify(
    db: DbSession,
    user_id: str,
    type: str,
    message: str,
    *,
    review_id: str | None = None,
    submission_id: str | None = None,
    menu: str | None = None,
) -> Notification:
    notification = Notification(
        id=new_id(db, "ntf"),
        user_id=user_id,
        type=type,
        message=message,
        review_id=review_id,
        submission_id=submission_id,
        menu=menu,
        created_at=utcnow(),
    )
    db.add(notification)
    return notification
