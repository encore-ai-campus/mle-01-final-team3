"""환경 설정. 값은 src/backend/.env 에서 읽는다 (.env.example 참고)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # 예: postgresql+psycopg2://사용자:비밀번호@localhost:5432/adguard
    database_url: str

    # local(개발) 또는 production(운영). 개발용 시드는 production에서 실행되지 않는다.
    app_env: str = "local"

    # 로그인 세션 만료: 로그인 시점부터 고정 10시간 (요청해도 연장하지 않음)
    session_hours: int = 10

    # 세션 쿠키를 HTTPS에서만 보낼지. 배포(HTTPS)에서는 true로 둔다.
    cookie_secure: bool = False

    # 요청을 허용할 프론트 주소 (CORS). .env에서는 JSON 배열로 쓴다: CORS_ORIGINS=["http://localhost:5173"]
    cors_origins: list[str] = ["http://localhost:5173"]

    # Agent가 완료 통지를 보낼 때 쓰는 서비스 토큰 (Authorization: Bearer {AGENT_TOKEN}). 비어 있으면 모두 거절.
    agent_token: str = ""

    # ----- 검토 흐름·Agent 연동 (API 설계서 3장·6장·7장) -----
    # 백엔드 → Agent 작업 요청 주소. POST {AGENT_URL}/internal/v1/review-jobs
    agent_url: str = "http://localhost:9000"

    # 작업 요청이 실패하면 같은 runId로 다시 보내기 전에 기다리는 시간(초). 모두 3번 보낸다.
    agent_send_retry_seconds: float = 1.0

    # 실행을 만든 뒤 이 시간 안에 완료 통지가 없으면 FAILED / RUN_TIMEOUT
    run_timeout_seconds: int = 180

    # 첨부 파일 저장 폴더 (git에 올리지 않음)
    attachment_dir: Path = BACKEND_DIR / "storage" / "attachments"

    # Agent가 첨부 파일을 내려받을 백엔드 주소 (서명 URL 앞부분)
    public_base_url: str = "http://localhost:8000"


settings = Settings()
