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


settings = Settings()
