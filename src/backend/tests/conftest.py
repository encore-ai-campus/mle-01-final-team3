"""검토 흐름 테스트 공통 준비.

- DB: 개발 DB와 섞이지 않게 테스트 전용 DB(기본: .env의 DATABASE_URL에서 DB 이름만 adguard_test)를 쓴다.
  없으면 만들고, 테스트 시작 때 테이블을 새로 만든다. TEST_DATABASE_URL로 바꿀 수 있다.
  테스트 DB의 시간대는 배포 DB처럼 UTC로 둔다. 응답 시각이 DB 시간대 설정에 기대지 않는지 확인하려는 것이다.
- Agent: 진짜 Agent 대신 가짜 Agent(FakeAgent)를 끼운다. 작업 요청을 기록하고, down=True면 연결 실패를 흉내 낸다.
  완료 통지는 테스트가 Agent 대신 POST /internal/v1/review-runs/{runId}/completion으로 보낸다.
- 로그인: 세션 행을 직접 만들어 쿠키(adguard_session)를 붙인다.

실행: src/backend 에서 `uv run pytest tests`
"""

import os
import secrets
import tempfile
from datetime import timedelta
from pathlib import Path

import psycopg2
import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
AGENT_TOKEN = "test-agent-token"


def _test_database_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    base = os.environ.get("DATABASE_URL") or dotenv_values(BACKEND_DIR / ".env").get("DATABASE_URL")
    if not base:
        pytest.exit("DATABASE_URL(.env) 또는 TEST_DATABASE_URL이 필요합니다.", returncode=2)
    return make_url(base).set(database="adguard_test").render_as_string(hide_password=False)


def _ensure_database(url: str) -> None:
    u = make_url(url)
    conn = psycopg2.connect(
        host=u.host, port=u.port or 5432, user=u.username, password=u.password, dbname="postgres"
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (u.database,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{u.database}"')
        cur.execute(f"ALTER DATABASE \"{u.database}\" SET timezone TO 'UTC'")
    conn.close()


TEST_DATABASE_URL = _test_database_url()
_ensure_database(TEST_DATABASE_URL)

# app을 import하기 전에 설정을 바꿔 둔다 (환경 변수가 .env보다 우선).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["AGENT_TOKEN"] = AGENT_TOKEN
os.environ["AGENT_TOKEN_EXTRA"] = ""  # .env에 교체용 토큰이 있어도 테스트는 토큰 하나로 시작한다
os.environ["AGENT_SEND_RETRY_SECONDS"] = "0"
os.environ["ATTACHMENT_DIR"] = tempfile.mkdtemp(prefix="adguard_att_")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.agent import client as agent_client  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.core.ids import new_id  # noqa: E402
from app.core.security import hash_token, new_session_token, utcnow  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Session, User  # noqa: E402

API = "/api/v1"
INTERNAL = "/internal/v1"


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables():
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} CASCADE"))
    yield


# ---------- 가짜 Agent ----------


class FakeAgent:
    """백엔드 → Agent 작업 요청을 받는 가짜. 판정은 하지 않고, 받은 요청을 기록만 한다."""

    def __init__(self) -> None:
        self.jobs: list[dict] = []  # 받은 작업 요청 (실패한 시도 포함)
        self.down = False  # True면 연결 실패를 흉내 낸다

    def send_review_job(self, job: dict) -> None:
        self.jobs.append(job)
        if self.down:
            raise ConnectionError("Agent 연결 실패 (가짜)")

    def last(self) -> dict:
        return self.jobs[-1]

    def sends_for(self, run_id: str) -> int:
        return sum(1 for j in self.jobs if j["runId"] == run_id)


@pytest.fixture(autouse=True)
def agent(monkeypatch) -> FakeAgent:
    fake = FakeAgent()
    monkeypatch.setattr(agent_client, "send_review_job", fake.send_review_job)
    return fake


@pytest.fixture
def agent_http() -> TestClient:
    """Agent가 백엔드로 완료 통지를 보낼 때 쓰는 클라이언트 (서비스 토큰)."""
    return TestClient(app, headers={"Authorization": f"Bearer {AGENT_TOKEN}"})


# ---------- 사용자 ----------


def _login_client(role: str, name: str) -> TestClient:
    with SessionLocal() as db:
        user = User(
            id=new_id(db, "usr"),
            name=name,
            email=f"{secrets.token_hex(4)}@test.local",
            password_hash="!",
            role=role,
            status="ACTIVE",
            must_change_password=False,
            created_at=utcnow(),
        )
        db.add(user)
        db.flush()
        token = new_session_token()
        now = utcnow()
        db.add(Session(token_hash=hash_token(token), user_id=user.id, created_at=now, expires_at=now + timedelta(hours=1)))
        db.commit()
        user_id = user.id
    c = TestClient(app)
    c.cookies.set("adguard_session", token)
    c.user_id = user_id  # type: ignore[attr-defined]
    return c


@pytest.fixture
def mkt() -> TestClient:
    return _login_client("MARKETING", "마케팅A")


@pytest.fixture
def mkt_b() -> TestClient:
    return _login_client("MARKETING", "마케팅B")


@pytest.fixture
def legal() -> TestClient:
    return _login_client("LEGAL", "법무A")


@pytest.fixture
def legal_b() -> TestClient:
    return _login_client("LEGAL", "법무B")


@pytest.fixture
def admin() -> TestClient:
    return _login_client("ADMIN", "관리자A")


# ---------- 인증·관리자 테스트용 ----------


@pytest.fixture
def db():
    """DB에 직접 데이터를 넣거나 확인할 때 쓰는 세션."""
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    """로그인하지 않은 브라우저. 로그인 API를 직접 호출해 쿠키를 받는다."""
    return TestClient(app)
