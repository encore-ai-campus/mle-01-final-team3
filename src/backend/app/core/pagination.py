"""목록 커서 페이지 (API 설계서 5장).

응답: {"items": [...], "nextCursor": "..." 또는 null}
- 정렬은 (정렬값, 행 ID) 순서로 고정한다.
- 커서는 필터·정렬에 묶인다. 조건이 바뀌었거나 잘못된 커서면 400 INVALID_CURSOR.

사용 예:
    rows, next_cursor = keyset_page(db, select(User), [User.name, User.id],
                                    limit=limit, cursor=cursor, filters={"q": q})
"""

import base64
import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Select, tuple_
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError


def _filters_hash(filters: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(filters, sort_keys=True, default=str).encode()).hexdigest()[:10]


def _to_json(v: Any) -> Any:
    return v.isoformat() if isinstance(v, datetime) else v


def keyset_page(
    db: DbSession,
    stmt: Select,
    cols: list,
    *,
    limit: int,
    cursor: str | None,
    filters: dict[str, Any],
    desc: bool = False,
) -> tuple[list, str | None]:
    fhash = _filters_hash(filters)
    if cursor:
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if data["h"] != fhash:
                raise ValueError("필터가 바뀜")
            last = [
                datetime.fromisoformat(v) if isinstance(c.type, DateTime) else v
                for c, v in zip(cols, data["k"], strict=True)
            ]
        except Exception:
            raise ApiError(400, "INVALID_CURSOR", "목록 위치가 만료되었습니다. 첫 페이지부터 다시 조회해 주세요.")
        stmt = stmt.where(tuple_(*cols) < tuple_(*last) if desc else tuple_(*cols) > tuple_(*last))

    stmt = stmt.order_by(*[c.desc() if desc else c.asc() for c in cols]).limit(limit + 1)
    rows = list(db.scalars(stmt).all())
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        key = [_to_json(getattr(rows[-1], c.key)) for c in cols]
        next_cursor = base64.urlsafe_b64encode(json.dumps({"k": key, "h": fhash}).encode()).decode()
    return rows, next_cursor
