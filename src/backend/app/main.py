"""백엔드 앱 시작점. 실행: src/backend 에서 `uv run uvicorn app.main:app --reload`

각 기능의 router는 여기에 한 줄씩 등록한다.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin_users.router import router as admin_users_router
from app.agent.completion import router as agent_completion_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.origin import add_origin_check
from app.legal.router import router as legal_router
from app.notifications.router import router as notifications_router
from app.reviews.actions import router as review_actions_router
from app.reviews.attachments import HideSignature
from app.reviews.attachments import internal_router as attachment_download_router
from app.reviews.attachments import router as attachments_router
from app.reviews.dashboard import router as dashboard_router
from app.reviews.lists import router as lists_router
from app.reviews.pdf import router as pdf_router
from app.reviews.router import router as reviews_router

API_PREFIX = "/api/v1"
INTERNAL_PREFIX = "/internal/v1"  # Agent 연동 (서비스 인증)

app = FastAPI(title="AdGuard AI 백엔드", version="5.0")
# 순서 주의: 나중에 등록한 미들웨어가 먼저 실행된다. CORS → 요청 ID → Origin 검사 순으로 돈다.
add_origin_check(app)  # 허용되지 않은 주소에서 온 POST·PATCH·DELETE는 403 (CSRF 보완)
register_error_handlers(app)

# 서버 접속 로그에 첨부 다운로드 주소의 서명(sig)이 남지 않게 가린다
logging.getLogger("uvicorn.access").addFilter(HideSignature())

# CORS: 프론트(다른 주소)에서 오는 요청과 로그인 쿠키를 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # 쿠키(adguard_session) 허용
    allow_methods=["*"],
    allow_headers=["*"],
    # 프론트 코드가 읽어야 하는 응답 헤더: PDF 파일명, 실행 조회 주소(202 Location), 오류 추적 ID
    expose_headers=["Content-Disposition", "Location", "X-Request-ID"],
)

app.include_router(auth_router, prefix=API_PREFIX, tags=["인증"])
app.include_router(admin_users_router, prefix=API_PREFIX, tags=["관리자"])
app.include_router(reviews_router, prefix=API_PREFIX, tags=["검토 흐름"])
app.include_router(attachments_router, prefix=API_PREFIX, tags=["검토 흐름"])
app.include_router(review_actions_router, prefix=API_PREFIX, tags=["검토 흐름"])
app.include_router(lists_router, prefix=API_PREFIX, tags=["검토함 목록"])
app.include_router(legal_router, prefix=API_PREFIX, tags=["법무 검토"])
app.include_router(notifications_router, prefix=API_PREFIX, tags=["알림"])
app.include_router(pdf_router, prefix=API_PREFIX, tags=["PDF"])
app.include_router(dashboard_router, prefix=API_PREFIX, tags=["대시보드"])
app.include_router(agent_completion_router, prefix=INTERNAL_PREFIX, tags=["Agent 연동 (내부)"])
app.include_router(attachment_download_router, prefix=INTERNAL_PREFIX, tags=["Agent 연동 (내부)"])
