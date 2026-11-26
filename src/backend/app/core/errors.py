"""공통 오류 응답. 형식은 API 설계서 7장을 따른다 (기표님 샘플 backend-test v5.2와 같은 규칙).

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "retryable": false,
    "requestId": "req_...",
    "fieldErrors": [{"field": "report.findings[0].sources", "code": "REQUIRED"}],
    "details": {...}          # 있을 때만 (예: 넘길 건 수)
  }
}

API 코드에서는 `raise ApiError(401, "UNAUTHENTICATED", "로그인이 필요합니다.")`처럼 쓴다.
"""

import logging
import secrets
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        field_errors: list[dict[str, str]] | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.field_errors = field_errors or []
        self.details = details


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    retryable: bool = False,
    field_errors: list[dict[str, str]] | None = None,
    details: Any = None,
) -> JSONResponse:
    error = {
        "code": code,
        "message": message,
        "retryable": retryable,
        "requestId": getattr(request.state, "request_id", "req_unknown"),
        "fieldErrors": field_errors or [],
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def field_path(loc) -> str:
    """('body', 'report', 'findings', 0, 'sources') → 'report.findings[0].sources'"""
    parts: list[str] = []
    for p in loc[1:]:
        if isinstance(p, int) and parts:
            parts[-1] = f"{parts[-1]}[{p}]"
        else:
            parts.append(str(p))
    return ".".join(parts) or "body"


def empty_code(err: dict) -> str:
    """빈 값(누락·null·빈 문자열)은 REQUIRED, 그 밖의 형식 오류는 INVALID."""
    if err["type"] in ("missing", "string_too_short", "too_short") or err.get("input") is None:
        return "REQUIRED"
    return "INVALID"


_HTTP_CODES = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "NOT_FOUND"}


def register_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = f"req_{secrets.token_hex(5)}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError):
        return error_response(
            request,
            exc.status_code,
            exc.code,
            exc.message,
            retryable=exc.retryable,
            field_errors=exc.field_errors,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        body_errors = [e for e in exc.errors() if e["loc"][:1] == ("body",)]
        if not body_errors:  # 쿼리·경로 값 오류
            return error_response(request, 400, "INVALID_QUERY", "조회 조건을 확인해 주세요.")
        fields = [{"field": field_path(e["loc"]), "code": empty_code(e)} for e in body_errors]
        return error_response(request, 422, "VALIDATION_ERROR", "입력값을 확인해 주세요.", field_errors=fields)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        return error_response(
            request, exc.status_code, _HTTP_CODES.get(exc.status_code, "ERROR"), str(exc.detail)
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.exception("처리하지 못한 오류 (requestId=%s)", getattr(request.state, "request_id", None))
        return error_response(request, 500, "INTERNAL_ERROR", "서버 오류가 발생했습니다.")
