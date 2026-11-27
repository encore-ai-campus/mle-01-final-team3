"""4단계: 같은 Idempotency-Key로 두 요청이 동시에 들어올 때 (app/core/idempotency.py).

검토 접수·재시도·AI 추천·법무 전송·의견 전송·종료·이관이 모두 run_idempotent 하나를 쓰므로 이 함수를 직접 확인한다.
두 요청이 모두 '처음 보는 키'라고 판단하고 일을 시작해도, 키 저장은 한쪽만 성공한다.
진 쪽은 자기 작업을 취소(롤백)하고 이긴 쪽의 응답을 그대로 돌려준다.
"""

import json
import threading

from sqlalchemy import func, select

from app.admin_users.service import create_user
from app.core.activity import log_activity
from app.core.db import SessionLocal
from app.core.errors import ApiError
from app.core.ids import new_id
from app.core.idempotency import run_idempotent
from app.models import ActivityLog, IdempotencyKey


def run_both_at_once(user_id: str, payload_a: dict, payload_b: dict) -> dict:
    """두 요청이 같은 키로 동시에 들어온 상황을 만든다.

    둘 다 '키 없음'을 확인하고 일(활동 로그 1줄 만들기)까지 마친 뒤에 저장하러 가도록 서로 기다리게 한다.
    """
    started = {"a": threading.Event(), "b": threading.Event()}
    results: dict = {}

    def request(name: str, other: str, payload: dict) -> None:
        with SessionLocal() as db:

            def work():
                log_activity(db, user_id, "REVIEW_REQUESTED", f"요청 {name}")
                started[name].set()
                started[other].wait(timeout=5)  # 상대도 일을 시작할 때까지 기다림
                return 202, {"runId": f"run_{name}"}

            try:
                resp = run_idempotent(db, user_id, "same-key", payload, work)
                results[name] = (resp.status_code, json.loads(resp.body))
            except ApiError as e:
                results[name] = (e.status_code, e.code)

    threads = [
        threading.Thread(target=request, args=("a", "b", payload_a)),
        threading.Thread(target=request, args=("b", "a", payload_b)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert not any(t.is_alive() for t in threads)
    return results


def setup_user(db) -> str:
    user = create_user(db, name="마케팅", email="m@test.com", role="MARKETING", password="password123")
    db.commit()
    new_id(db, "log")  # 번호표 기계(시퀀스)를 미리 만들어 둔다
    db.commit()
    return user.id


def test_same_key_same_request_at_once_is_processed_once(db):
    uid = setup_user(db)
    results = run_both_at_once(uid, {"title": "광고"}, {"title": "광고"})

    # 두 요청 모두 같은 응답 (먼저 저장한 쪽의 응답)
    assert results["a"] == results["b"]
    assert results["a"][0] == 202
    # 일은 한 번만 반영됨: 진 쪽이 만든 활동 로그는 취소됨
    assert db.scalar(select(func.count()).select_from(ActivityLog)) == 1
    assert db.scalar(select(func.count()).select_from(IdempotencyKey)) == 1
    winner = db.scalar(select(ActivityLog.target_label))
    assert results["a"][1] == {"runId": f"run_{winner[-1]}"}  # 남은 로그와 응답이 같은 요청에서 나옴


def test_same_key_different_request_at_once_is_409(db):
    uid = setup_user(db)
    results = run_both_at_once(uid, {"title": "광고 A"}, {"title": "광고 B"})

    # 한쪽은 처리되고, 다른 쪽은 409 STATE_CONFLICT
    assert sorted(status for status, _ in results.values()) == [202, 409]
    assert (409, "STATE_CONFLICT") in results.values()
    assert db.scalar(select(func.count()).select_from(ActivityLog)) == 1
