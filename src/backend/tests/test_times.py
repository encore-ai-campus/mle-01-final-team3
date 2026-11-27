"""API 시각 규칙 (app/core/times.py).

- 응답: 한국시간 ISO 8601, 초 단위 (예: 2026-11-27T09:45:16+09:00). DB 시간대 설정과 상관없이 같다.
- 요청: 오프셋이 없는 시각은 한국시간으로 본다.
테스트 DB는 UTC 시간대라서, 변환을 빠뜨리면 +00:00이 나와 실패한다.
"""

import re
from datetime import datetime, timezone

from sqlalchemy import update

from app.core.db import SessionLocal
from app.core.ids import new_id
from app.core.times import assume_kst, to_kst
from app.models import ActivityLog, User
from tests.helpers import API, detail, finish, new_review, run_of

KST_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")

# 2026-11-27 00:30:05 한국시간 = 2026-11-26 15:30:05 UTC
AT_UTC = datetime(2026, 11, 26, 15, 30, 5, 123456, tzinfo=timezone.utc)
AT_KST = "2026-11-27T00:30:05+09:00"


def test_to_kst_converts_and_drops_microseconds():
    assert to_kst(AT_UTC).isoformat() == AT_KST
    assert to_kst(AT_UTC.replace(tzinfo=None)).isoformat() == AT_KST  # 시간대 없는 값 = UTC로 저장된 값
    assert to_kst(None) is None


def test_assume_kst_only_fills_missing_offset():
    assert assume_kst(datetime(2026, 11, 27)).isoformat() == "2026-11-27T00:00:00+09:00"
    assert assume_kst(AT_UTC) is AT_UTC
    assert assume_kst(None) is None


def test_review_and_run_times_are_kst_seconds(mkt, agent_http):
    rev, run = new_review(mkt)
    finish(agent_http, run, rev)
    r = run_of(mkt, run)
    for key in ("updatedAt", "startedAt", "finishedAt"):
        assert KST_SECONDS.match(r[key]), r[key]
    assert KST_SECONDS.match(detail(mkt, rev)["createdAt"])


def _log_at(user_id: str, at: datetime) -> None:
    with SessionLocal() as db:
        db.add(ActivityLog(id=new_id(db, "log"), user_id=user_id, operation="LOGIN", occurred_at=at))
        db.commit()


def test_admin_activity_times_are_kst(admin, mkt):
    _log_at(mkt.user_id, AT_UTC)
    with SessionLocal() as db:
        db.execute(update(User).where(User.id == mkt.user_id).values(last_login_at=AT_UTC))
        db.commit()

    body = admin.get(f"{API}/admin/users/{mkt.user_id}/activity").json()
    assert [i["occurredAt"] for i in body["items"]] == [AT_KST]
    assert body["user"]["lastLoginAt"] == AT_KST


def test_admin_activity_filter_without_offset_is_kst(admin, mkt):
    _log_at(mkt.user_id, AT_UTC)  # 한국 날짜로 11/27
    url = f"{API}/admin/users/{mkt.user_id}/activity"

    def items(frm: str, to: str) -> list:
        r = admin.get(url, params={"from": frm, "to": to})
        assert r.status_code == 200
        return r.json()["items"]

    # 한국 날짜 11/27 하루에는 들어가고 (UTC로 해석하면 빠진다), 11/26 하루에는 빠진다
    assert len(items("2026-11-27T00:00:00", "2026-11-28T00:00:00")) == 1
    assert items("2026-11-26T00:00:00", "2026-11-27T00:00:00") == []
    # 오프셋을 붙여 보내면 그대로 쓴다
    assert len(items("2026-11-26T15:00:00Z", "2026-11-26T16:00:00Z")) == 1
