"""중복 요청 방지 (Idempotency-Key). API 설계서 7장.

같은 사용자가 같은 키로 다시 보내면 처음 응답을 그대로 돌려주고, 일은 한 번만 한다.
- 키가 없으면: 중복 방지 없이 평소처럼 처리 (팀 합의)
- 같은 키 + 다른 내용: 409 STATE_CONFLICT (팀 합의. 다른 충돌과 구분이 필요해지면 IDEMPOTENCY_KEY_REUSED로 바꿈)

사용 예 (검토 흐름 API도 같은 방식):

    @router.post("/reviews")
    def create_review(body: ReviewCreate, user: Marketer, db=Depends(get_db), idempotency_key: IdemKey = None):
        def work():
            ...                      # DB 변경 (commit 하지 않음)
            return 202, {...}        # (상태 코드, 응답 본문)
        return run_idempotent(db, user.id, idempotency_key, body.model_dump(), work)

work 안의 변경과 키 저장을 한 트랜잭션으로 commit 한다.
"""

import hashlib
import json
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.core.security import utcnow
from app.models import IdempotencyKey

IdemKey = Annotated[str | None, Header(alias="Idempotency-Key", max_length=100)]


def _reused_key() -> ApiError:
    return ApiError(409, "STATE_CONFLICT", "같은 요청 번호로 다른 내용을 보냈습니다. 화면을 새로고침한 뒤 다시 시도해 주세요.")


def _response(status_code: int, content: Any) -> Response:
    if status_code == 204:
        return Response(status_code=204)
    return JSONResponse(content, status_code=status_code)


def run_idempotent(
    db: DbSession,
    user_id: str,
    key: str | None,
    payload: Any,
    work: Callable[[], tuple[int, Any]],
) -> Response:
    if not key:
        status_code, body = work()
        db.commit()
        return _response(status_code, jsonable_encoder(body))

    request_hash = hashlib.sha256(
        json.dumps(jsonable_encoder(payload), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()

    found = db.get(IdempotencyKey, (user_id, key))
    if found is not None:
        if found.request_hash != request_hash:
            raise _reused_key()
        return _response(found.status_code, found.response)

    status_code, body = work()
    content = jsonable_encoder(body)
    db.add(
        IdempotencyKey(
            user_id=user_id,
            key=key,
            request_hash=request_hash,
            status_code=status_code,
            response=content,
            created_at=utcnow(),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # 같은 키 요청이 동시에 들어와 다른 쪽이 먼저 저장한 경우
        db.rollback()
        found = db.get(IdempotencyKey, (user_id, key))
        if found is None:
            raise
        if found.request_hash != request_hash:
            raise _reused_key()
        return _response(found.status_code, found.response)
    return _response(status_code, content)
