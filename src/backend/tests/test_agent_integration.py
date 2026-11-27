"""Agent 담당과 정한 연동 규칙: 작업 요청 응답(202·200), 서비스 토큰 교체, 접속 로그의 서명 가리기."""

import logging
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient

from app.agent import client as agent_client
from app.agent.client import send_review_job as real_send_review_job  # autouse 가짜 Agent로 바뀌기 전의 실제 함수
from app.core.config import settings
from app.main import app
from app.reviews.attachments import HideSignature
from tests.conftest import AGENT_TOKEN
from tests.helpers import API, INTERNAL, TEMP_ERROR, new_review

NEW_TOKEN = "test-agent-token-new"


# ---------- 작업 요청 응답 ----------


@pytest.fixture
def agent_answers(monkeypatch):
    """실제 send_review_job이 부르는 httpx.post를 바꿔, Agent가 정해진 상태 코드로 답하게 한다."""
    sent: list[dict] = []

    def answer_with(status: int):
        def fake_post(url, json, headers, timeout):
            sent.append({"url": url, "json": json, "headers": headers})
            return httpx.Response(status, json={"runId": json["runId"]})

        monkeypatch.setattr(agent_client.httpx, "post", fake_post)

    return answer_with, sent


@pytest.mark.parametrize("status", [202, 200])
def test_agent_202_or_200_is_accepted(agent_answers, status):
    """202: 처음 받음·진행 중, 200: 이미 끝난 runId(다시 실행하지 않음). 둘 다 접수로 보고 다시 보내지 않는다."""
    answer_with, sent = agent_answers
    answer_with(status)
    real_send_review_job({"runId": "run_001"})
    assert len(sent) == 1
    assert sent[0]["url"].endswith("/internal/v1/review-jobs")
    assert sent[0]["headers"]["Authorization"] == f"Bearer {AGENT_TOKEN}"


@pytest.mark.parametrize("status", [400, 401, 409, 500, 503])
def test_other_agent_status_is_rejected(agent_answers, status):
    """그 밖의 응답은 실패로 보고 dispatch가 같은 runId로 다시 보낸다 (3번 다 실패하면 AGENT_UNAVAILABLE)."""
    answer_with, _ = agent_answers
    answer_with(status)
    with pytest.raises(agent_client.AgentRejected):
        real_send_review_job({"runId": "run_001"})


def test_job_sent_with_200_marks_running(mkt, agent_answers, monkeypatch):
    """실제 클라이언트로 끝까지: Agent가 200(이미 끝남)으로 답해도 실행은 AGENT_UNAVAILABLE이 되지 않는다."""
    answer_with, sent = agent_answers
    answer_with(200)
    monkeypatch.setattr(agent_client, "send_review_job", real_send_review_job)
    _, run = new_review(mkt)
    assert len(sent) == 1  # 다시 보내지 않았다
    r = mkt.get(f"{API}/review-runs/{run}").json()
    assert r["runStatus"] == "RUNNING" and r["error"] is None


# ---------- 서비스 토큰 교체 ----------


def _completion(token: str, run: str, rev: str):
    body = {"schemaVersion": "1.0", "reviewId": rev, "runStatus": "FAILED", "error": TEMP_ERROR}
    return TestClient(app, headers={"Authorization": f"Bearer {token}"}).post(
        f"{INTERNAL}/review-runs/{run}/completion", json=body
    )


def test_rotation_accepts_both_tokens(mkt, monkeypatch):
    """1단계: 받는 토큰에 새 토큰을 더한다. 이전 토큰·새 토큰 모두 200, 모르는 토큰은 401."""
    monkeypatch.setattr(settings, "agent_token_extra", NEW_TOKEN)
    rev, run = new_review(mkt)
    assert _completion("wrong", run, rev).status_code == 401
    assert _completion(NEW_TOKEN, run, rev).status_code == 200
    assert _completion(AGENT_TOKEN, run, rev).status_code == 200  # 같은 통지 재전송 → 200


def test_without_extra_only_current_token(mkt):
    rev, run = new_review(mkt)
    assert _completion(NEW_TOKEN, run, rev).status_code == 401
    assert _completion(AGENT_TOKEN, run, rev).status_code == 200


def test_empty_tokens_reject_everything(mkt, monkeypatch):
    rev, run = new_review(mkt)
    monkeypatch.setattr(settings, "agent_token", "")
    assert _completion("", run, rev).status_code == 401
    assert _completion(AGENT_TOKEN, run, rev).status_code == 401


def test_signed_url_survives_token_switch(mkt, agent, monkeypatch):
    """2단계에서 보내는 토큰을 새 토큰으로 바꿔도, 바꾸기 전에 발급한 첨부 URL은 10분 동안 그대로 쓸 수 있다."""
    att = mkt.post(
        f"{API}/attachments", files={"file": ("근거자료.pdf", b"%PDF-1.4 test")}, data={"purpose": "AD_COPY"}
    ).json()["attachmentId"]
    new_review(mkt, attachmentIds=[att])
    old_url = urlsplit(agent.last()["attachments"][0]["url"])  # 이전 토큰으로 서명됨

    # 2단계: 보내는 토큰 = 새 토큰, 이전 토큰은 받는 토큰으로만 남긴다
    monkeypatch.setattr(settings, "agent_token", NEW_TOKEN)
    monkeypatch.setattr(settings, "agent_token_extra", AGENT_TOKEN)
    assert TestClient(app).get(f"{old_url.path}?{old_url.query}").status_code == 200

    # 3단계: 이전 토큰을 지우면 이전 토큰으로 서명한 URL은 401
    monkeypatch.setattr(settings, "agent_token_extra", "")
    assert TestClient(app).get(f"{old_url.path}?{old_url.query}").status_code == 401


# ---------- 접속 로그의 서명 가리기 ----------


def _access_record(path: str) -> logging.LogRecord:
    """uvicorn이 접속 로그를 남기는 모양: '%s - "%s %s HTTP/%s" %d' % (주소, 메서드, 경로+쿼리, 버전, 상태)."""
    return logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 0, '%s - "%s %s HTTP/%s" %d', ("127.0.0.1:5000", "GET", path, "1.1", 200), None
    )


def test_access_log_hides_signature():
    record = _access_record("/internal/v1/attachments/att_001?expires=1795688778&sig=0123abcd")
    assert HideSignature().filter(record) is True  # 로그는 남기고 내용만 가린다
    line = record.getMessage()
    assert "0123abcd" not in line
    assert line == '127.0.0.1:5000 - "GET /internal/v1/attachments/att_001?expires=1795688778&sig=*** HTTP/1.1" 200'
    assert record.args[4] == 200  # uvicorn 포매터가 쓰는 칸 모양은 그대로


def test_access_log_other_paths_unchanged():
    record = _access_record("/api/v1/reviews?status=OPEN")
    HideSignature().filter(record)
    assert record.getMessage() == '127.0.0.1:5000 - "GET /api/v1/reviews?status=OPEN HTTP/1.1" 200'


def test_filter_attached_to_uvicorn_access_logger():
    assert any(isinstance(f, HideSignature) for f in logging.getLogger("uvicorn.access").filters)
