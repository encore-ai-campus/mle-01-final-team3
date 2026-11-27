"""첨부 파일. 설계서 6장 '[파일 첨부]'.

- POST /api/v1/attachments: 마케팅 담당자가 파일을 1개씩 올린다 (.pdf·.xlsx·.docx).
- 검토 요청(POST /reviews)에는 attachmentIds만 보낸다. 합계 10MB를 넘으면 413.
- Agent에는 작업 요청의 attachments[].url로 10분짜리 서명 URL을 준다.
  GET /internal/v1/attachments/{attachmentId}?expires=..&sig=.. 로 내려받는다.
"""

import hashlib
import hmac
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.deps import Marketer, get_db
from app.core.errors import ApiError
from app.core.ids import new_id
from app.core.security import utcnow
from app.models import Attachment, ReviewAttachment, User

router = APIRouter()
internal_router = APIRouter()

LIMIT_BYTES = 10 * 1024 * 1024  # 제출당 합계 10MB
FILENAME_MAX = 255  # attachments.filename String(255)
# attachments.content_type에는 파일 종류(pdf·xlsx·docx)를 저장하고, 내려받을 때 MIME 타입으로 바꾼다.
MEDIA_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
SIGNED_URL_SECONDS = 600  # 10분
_CHUNK = 1024 * 1024


def _too_large() -> ApiError:
    return ApiError(413, "ATTACHMENT_LIMIT_EXCEEDED", "첨부 파일은 합계 10MB까지 올릴 수 있습니다.")


def _file_path(storage_key: str) -> Path:
    return Path(settings.attachment_dir) / storage_key


@router.post(
    "/attachments",
    status_code=201,
    summary="[파일 첨부] (M-8)",
    description=".pdf·.xlsx·.docx만. 형식 오류 415 UNSUPPORTED_FILE_TYPE(M-13), 10MB 초과 413 ATTACHMENT_LIMIT_EXCEEDED(M-14)",
)
def upload_attachment(
    user: Marketer,
    file: UploadFile = File(...),
    purpose: Literal["AD_COPY"] = Form("AD_COPY"),
    db: DbSession = Depends(get_db),
):
    filename = Path(file.filename or "").name
    ext = Path(filename).suffix.lower()
    file_type = ext.removeprefix(".")
    if file_type not in MEDIA_TYPES:
        raise ApiError(415, "UNSUPPORTED_FILE_TYPE", "PDF, Excel, Word 파일만 첨부할 수 있습니다.")
    if len(filename) > FILENAME_MAX:
        raise ApiError(
            422, "VALIDATION_ERROR", f"파일 이름은 {FILENAME_MAX}자까지 쓸 수 있습니다.",
            field_errors=[{"field": "file", "code": "INVALID"}],
        )  # fmt: skip

    attachment_id = new_id(db, "att")
    storage_key = f"{attachment_id}{ext}"
    path = _file_path(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with path.open("wb") as out:
            while chunk := file.file.read(_CHUNK):
                size += len(chunk)
                if size > LIMIT_BYTES:
                    raise _too_large()
                out.write(chunk)
        db.add(
            Attachment(
                id=attachment_id,
                filename=filename,
                content_type=file_type,
                size=size,
                storage_key=storage_key,
                uploaded_by=user.id,
                created_at=utcnow(),
            )
        )
        db.commit()
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {"attachmentId": attachment_id, "filename": filename, "size": size}


def check_review_attachments(db: DbSession, user: User, attachment_ids: list[str]) -> list[str]:
    """검토 요청에 붙일 파일 확인. 없는 파일·남이 올린 파일·이미 다른 검토 건에 붙은 파일은 422, 합계 10MB 초과는 413."""
    ids = list(dict.fromkeys(attachment_ids))  # 중복 제거, 순서 유지
    if not ids:
        return []
    found = {a.id: a for a in db.scalars(select(Attachment).where(Attachment.id.in_(ids)))}
    used = set(db.scalars(select(ReviewAttachment.attachment_id).where(ReviewAttachment.attachment_id.in_(ids))))
    bad = [
        {"field": f"attachmentIds[{i}]", "code": "INVALID"}
        for i, aid in enumerate(ids)
        if aid not in found or found[aid].uploaded_by != user.id or aid in used
    ]
    if bad:
        raise ApiError(422, "VALIDATION_ERROR", "첨부 파일을 다시 올려 주세요.", field_errors=bad)
    if sum(found[aid].size for aid in ids) > LIMIT_BYTES:
        raise _too_large()
    return ids


# ---------- Agent용 서명 URL ----------


def _signature(attachment_id: str, expires: int) -> str:
    return hmac.new(settings.agent_token.encode(), f"{attachment_id}:{expires}".encode(), hashlib.sha256).hexdigest()


def signed_url(attachment_id: str) -> str:
    expires = int(time.time()) + SIGNED_URL_SECONDS
    base = settings.public_base_url.rstrip("/")
    return f"{base}/internal/v1/attachments/{attachment_id}?expires={expires}&sig={_signature(attachment_id, expires)}"


@internal_router.get(
    "/attachments/{attachmentId}",
    summary="첨부 파일 내려받기 (Agent, 서명 URL)",
    description="작업 요청의 attachments[].url. 10분 유효. 서명이 틀리거나 만료되면 401",
    response_class=FileResponse,
)
def download_attachment(
    attachmentId: str,
    expires: int = Query(...),
    sig: str = Query(...),
    db: DbSession = Depends(get_db),
):
    valid = (
        settings.agent_token
        and expires >= int(time.time())
        and hmac.compare_digest(sig, _signature(attachmentId, expires))
    )
    if not valid:
        raise ApiError(401, "UNAUTHENTICATED", "파일 주소가 만료되었거나 올바르지 않습니다.")
    attachment = db.get(Attachment, attachmentId)
    if attachment is None or not _file_path(attachment.storage_key).is_file():
        raise ApiError(404, "NOT_FOUND", "파일을 찾을 수 없습니다.")
    return FileResponse(
        _file_path(attachment.storage_key), media_type=MEDIA_TYPES.get(attachment.content_type, "application/octet-stream"), filename=attachment.filename
    )
