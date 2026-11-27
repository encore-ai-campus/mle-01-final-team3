"""백엔드 → Agent 작업 요청 1번. POST {AGENT_URL}/internal/v1/review-jobs

Agent 응답 (Agent 담당과 합의)
- 202: 처음 받았거나 이미 진행 중인 runId. 같은 runId를 다시 받아도 작업을 두 번 시작하지 않는다.
- 200: 이미 끝난 runId. 다시 실행하지 않고 현재 상태를 돌려준다. 결과는 완료 통지로 온다
  (완료 통지를 못 보냈으면 Agent가 저장해 둔 같은 결과를 다시 보낸다).
- 둘 다 접수로 보고 재전송을 멈춘다. 백엔드는 200의 본문을 쓰지 않는다 (결과는 완료 통지로만 받는다).

테스트는 이 함수를 가짜 Agent로 바꿔 끼운다 (tests/conftest.py).
"""

import httpx

from app.core.config import settings

ACCEPTED_STATUS = (202, 200)


class AgentRejected(Exception):
    """Agent가 202·200이 아닌 응답을 줬다."""


def send_review_job(job: dict) -> None:
    """202·200이면 그대로 끝, 연결 오류·응답 없음·그 밖의 응답이면 예외."""
    resp = httpx.post(
        f"{settings.agent_url.rstrip('/')}/internal/v1/review-jobs",
        json=job,
        headers={"Authorization": f"Bearer {settings.agent_token}"},
        timeout=10,
    )
    if resp.status_code not in ACCEPTED_STATUS:
        raise AgentRejected(f"Agent 접수 실패: HTTP {resp.status_code}")
