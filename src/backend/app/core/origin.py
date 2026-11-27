"""Origin 검사 (CSRF 토큰 대신 쓰는 보완책).

브라우저는 요청마다 "어느 사이트 화면에서 출발했는지"를 Origin 헤더에 적고, 웹페이지는 이 값을 바꿀 수 없다.
데이터를 바꾸는 요청(POST·PUT·PATCH·DELETE)의 Origin이 허용된 프론트 주소(CORS_ORIGINS)나
백엔드 자기 주소(Swagger)가 아니면 403으로 거절한다.

- Origin이 없는 요청(curl, 테스트 등 브라우저가 아닌 호출)은 통과시킨다. 다른 사이트가 사용자의 쿠키를
  몰래 쓰는 공격(CSRF)은 브라우저에서만 일어나고, 브라우저는 이런 요청에 항상 Origin을 붙인다.
- Agent 내부 API(/internal)는 쿠키가 아니라 서비스 토큰으로 인증하므로 검사하지 않는다.
"""

from urllib.parse import urlsplit

from fastapi import FastAPI, Request

from app.core.config import settings
from app.core.errors import error_response

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def origin_allowed(request: Request) -> bool:
    origin = request.headers.get("origin")
    if origin is None:
        return True
    if origin in {o.rstrip("/") for o in settings.cors_origins}:
        return True
    return urlsplit(origin).netloc == request.headers.get("host")  # 백엔드 자기 주소 (Swagger)


def add_origin_check(app: FastAPI) -> None:
    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        if request.method in UNSAFE_METHODS and request.url.path.startswith("/api/") and not origin_allowed(request):
            return error_response(request, 403, "FORBIDDEN", "허용되지 않은 주소에서 보낸 요청입니다.")
        return await call_next(request)
