"""백엔드 → Agent 작업 요청 1번. POST {AGENT_URL}/internal/v1/review-jobs, 접수되면 202.

테스트는 이 함수를 가짜 Agent로 바꿔 끼운다 (tests/conftest.py).
"""

import httpx

from app.core.config import settings


class AgentRejected(Exception):
    """Agent가 202가 아닌 응답을 줬다."""


def send_review_job(job: dict) -> None:
    """202면 그대로 끝, 연결 오류·응답 없음·202가 아니면 예외."""
    resp = httpx.post(
        f"{settings.agent_url.rstrip('/')}/internal/v1/review-jobs",
        json=job,
        headers={"Authorization": f"Bearer {settings.agent_token}"},
        timeout=10,
    )
    if resp.status_code != 202:
        raise AgentRejected(f"Agent 접수 실패: HTTP {resp.status_code}")
