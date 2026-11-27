"""알림 API. 설계서 5장 '알림·마이페이지·PDF'.

GET  /notifications/summary     종·사이드바 파란 불 (M-63·LG-34·M-74·LG-40): unreadCount, menuBadges {inbox, sentList}
GET  /notifications             종 클릭 '알림' 패널 (M-64·LG-35). 최신순, readAt=null이면 '새 알림'
POST /notifications/read-all    [모두 읽음] (M-65·LG-36)
POST /notifications/menu-seen   '검토함'·'법무팀 전송 내역' 진입 (M-66). 그 메뉴의 파란 불만 끈다

- 종의 파란 불(unreadCount)은 안 읽은 알림 수, 메뉴의 파란 불(menuBadges)은 그 메뉴에 마지막으로 들어간 뒤 새 알림이 왔는지다.
  둘은 따로 꺼진다. 메뉴에 들어가도 알림은 안 읽은 채로 남고, [모두 읽음]을 눌러도 메뉴 파란 불은 그대로다.
- 법무는 sentList 메뉴가 없어 inbox만 쓴다 (sentList는 항상 false).
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import exists, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from app.core.deps import CurrentUser, get_db
from app.core.pagination import keyset_page
from app.core.schemas import CamelModel
from app.core.security import utcnow
from app.core.times import to_kst
from app.models import MenuSeen, Notification, User

router = APIRouter(prefix="/notifications")

Menu = Literal["INBOX", "SENT_LIST"]


class MenuSeenRequest(CamelModel):
    menu: Menu


def _unread_count(db: DbSession, user_id: str) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )


def _menu_badge(db: DbSession, user_id: str, menu: str) -> bool:
    """마지막으로 그 메뉴에 들어간 뒤(처음이면 언제든) 그 메뉴 알림이 왔으면 true."""
    seen_at = db.scalar(select(MenuSeen.seen_at).where(MenuSeen.user_id == user_id, MenuSeen.menu == menu))
    cond = [Notification.user_id == user_id, Notification.menu == menu]
    if seen_at is not None:
        cond.append(Notification.created_at > seen_at)
    return bool(db.scalar(select(exists().where(*cond))))


def summary_view(db: DbSession, user: User) -> dict:
    return {
        "unreadCount": _unread_count(db, user.id),
        "menuBadges": {
            "inbox": _menu_badge(db, user.id, "INBOX"),
            "sentList": _menu_badge(db, user.id, "SENT_LIST") if user.role == "MARKETING" else False,
        },
    }


def notification_view(n: Notification) -> dict:
    # target: 알림을 눌렀을 때 열 보고서. 법무 알림은 법무 요청 건(submissionId), 마케팅 알림은 검토 건(reviewId). 계정 알림은 null
    if n.type in ("SUBMISSION_RECEIVED", "LEGAL_REASSIGN_NEEDED"):
        target = n.submission_id
    else:
        target = n.review_id
    return {
        "notificationId": n.id,
        "type": n.type,
        "message": n.message,
        "target": target,
        "createdAt": to_kst(n.created_at),
        "readAt": to_kst(n.read_at),
    }


@router.get("/summary", summary="종·사이드바 파란 불 (M-63·LG-34)")
def get_summary(user: CurrentUser, db: DbSession = Depends(get_db)) -> dict:
    return summary_view(db, user)


@router.get(
    "",
    summary="알림 목록 (M-64·LG-35)",
    description="최신순(같으면 notificationId). readAt=null은 '새 알림', 나머지는 '지난 알림'. 없으면 빈 배열. "
    "목록 공통 형식 {items, nextCursor}, limit 기본 20·최대 100",
)
def list_notifications(
    user: CurrentUser,
    db: DbSession = Depends(get_db),
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    stmt = select(Notification).where(Notification.user_id == user.id)
    rows, next_cursor = keyset_page(
        db, stmt, [Notification.created_at, Notification.id], limit=limit, cursor=cursor,
        filters={"user": user.id}, desc=True,
    )  # fmt: skip
    return {"items": [notification_view(n) for n in rows], "nextCursor": next_cursor}


@router.post("/read-all", summary="[모두 읽음] (M-65·LG-36)")
def read_all(user: CurrentUser, db: DbSession = Depends(get_db)) -> dict:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=utcnow())
    )
    db.commit()
    return {"unreadCount": 0}


@router.post(
    "/menu-seen",
    summary="메뉴 진입 → 그 메뉴 파란 불 끄기 (M-66)",
    description="menu=INBOX('검토함') 또는 SENT_LIST('법무팀 전송 내역'). 응답은 /notifications/summary와 같은 모양",
)
def menu_seen(body: MenuSeenRequest, user: CurrentUser, db: DbSession = Depends(get_db)) -> dict:
    now = utcnow()
    stmt = insert(MenuSeen).values(user_id=user.id, menu=body.menu, seen_at=now)
    db.execute(stmt.on_conflict_do_update(index_elements=["user_id", "menu"], set_={"seen_at": now}))
    db.commit()
    return summary_view(db, user)
