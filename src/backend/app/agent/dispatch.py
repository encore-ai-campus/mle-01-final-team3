"""실행을 Agent에 보낸다. 202 응답을 보낸 뒤 백그라운드에서 돈다 (설계서 3장 '실행 상태').

- Agent가 202(접수·진행 중) 또는 200(이미 끝남)으로 답하면 QUEUED → RUNNING (startedAt 기록). 응답 규칙은 client.py
- 연결 오류·응답 없음·그 밖의 응답이면 같은 runId로 다시 보낸다. 모두 3번 보내고도 안 되면 FAILED / AGENT_UNAVAILABLE
- 그 사이 완료 통지나 시간 초과로 이미 확정된 실행은 건드리지 않는다
"""

import logging
import time

from app.agent import client
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import utcnow
from app.models import ReviewRun
from app.reviews import codes as C
from app.reviews.runs import UNAVAILABLE_MESSAGE, build_job, fail_run

logger = logging.getLogger(__name__)

SEND_TRIES = 3  # 작업 요청 1번 + 같은 runId로 재전송 2번


def dispatch_run(run_id: str) -> None:
    with SessionLocal() as db:
        run = db.get(ReviewRun, run_id)
        if run is None or run.status != C.QUEUED:
            return
        job = build_job(db, run)

    accepted = False
    for i in range(SEND_TRIES):
        if i:
            time.sleep(settings.agent_send_retry_seconds)
        try:
            client.send_review_job(job)
        except Exception as exc:  # noqa: BLE001 - 어떤 실패든 같은 규칙으로 재전송
            logger.warning("Agent 작업 요청 실패 (runId=%s, %d/%d): %s", run_id, i + 1, SEND_TRIES, exc)
            continue
        accepted = True
        break

    with SessionLocal() as db:
        run = db.get(ReviewRun, run_id, with_for_update=True)
        if run is None:
            return
        if accepted:
            if run.status == C.QUEUED:
                now = utcnow()
                run.status, run.started_at, run.updated_at = C.RUNNING, now, now
        elif run.status in C.ACTIVE:
            fail_run(db, run, C.AGENT_UNAVAILABLE, UNAVAILABLE_MESSAGE, True)
        db.commit()
