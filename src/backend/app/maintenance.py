"""정리 명령: 오래된 중복 방지 키와 남는 첨부 파일을 지운다.

실행: src/backend 에서 `uv run python -m app.maintenance`
      지우지 않고 지울 개수만 보려면 `uv run python -m app.maintenance --dry-run`
배포 서버에서는 하루 한 번 예약 실행한다.

지우는 것
1. 중복 방지 키(idempotency_keys): 만든 지 24시간이 지난 키
2. 검토 건에 연결되지 않은 첨부: 올린 지 24시간이 지나도록 검토 요청에 쓰이지 않은 파일.
   DB 행을 지우고 커밋한 뒤 파일을 지운다 (설계서 3장: DB 밖 데이터는 커밋이 성공한 뒤에 지운다).
3. DB에 없는 파일: 첨부 폴더에 있지만 attachments 행이 없는 파일.
   저장 중 서버가 멈췄거나, 2번에서 커밋 뒤 파일 삭제가 실패한 경우다 (설계서 3장: 실패하면 정리 작업에서 다시 지운다).
   올리는 중인 파일을 지우지 않도록 마지막으로 바뀐 지 1시간이 지난 것만 지운다.
"""

import argparse
import logging
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import utcnow
from app.models import Attachment, IdempotencyKey, ReviewAttachment

logger = logging.getLogger(__name__)

KEY_TTL = timedelta(hours=24)  # 중복 방지 키 보관 기간
UNATTACHED_TTL = timedelta(hours=24)  # 검토 건에 연결되지 않은 첨부를 남겨 두는 기간
ORPHAN_FILE_AGE = timedelta(hours=1)  # DB에 없는 파일을 지우기 전 기다리는 시간 (올리는 중인 파일 보호)


def delete_old_idempotency_keys(db: DbSession, *, dry_run: bool = False) -> int:
    """만든 지 24시간이 지난 중복 방지 키를 지운다. 지운(지울) 개수를 돌려준다."""
    cutoff = utcnow() - KEY_TTL
    if dry_run:
        return db.scalar(select(func.count()).select_from(IdempotencyKey).where(IdempotencyKey.created_at < cutoff))
    result = db.execute(delete(IdempotencyKey).where(IdempotencyKey.created_at < cutoff))
    db.commit()
    return result.rowcount


def delete_unattached_attachments(db: DbSession, *, dry_run: bool = False) -> int:
    """올린 지 24시간이 지나도록 검토 건에 연결되지 않은 첨부를 지운다 (DB 행 → 커밋 → 파일)."""
    cutoff = utcnow() - UNATTACHED_TTL
    targets = db.scalars(
        select(Attachment).where(
            Attachment.created_at < cutoff,
            ~exists().where(ReviewAttachment.attachment_id == Attachment.id),
        )
    ).all()
    if dry_run:
        return len(targets)

    deleted = 0
    for att in targets:
        storage_key = att.storage_key
        try:
            db.delete(att)
            db.commit()
        except IntegrityError:
            # 정리하는 사이에 검토 요청에 연결된 파일이다. 그대로 둔다
            db.rollback()
            continue
        deleted += 1
        try:
            _attachment_path(storage_key).unlink(missing_ok=True)
        except OSError as exc:  # 남은 파일은 다음 정리 때 'DB에 없는 파일'로 지운다
            logger.warning("첨부 파일 삭제 실패 (%s): %s", storage_key, exc)
    return deleted


def delete_orphan_files(db: DbSession, *, dry_run: bool = False) -> int:
    """첨부 폴더에 있지만 attachments 행이 없는 파일 중, 바뀐 지 1시간이 지난 것을 지운다."""
    folder = Path(settings.attachment_dir)
    if not folder.is_dir():
        return 0
    known = set(db.scalars(select(Attachment.storage_key)).all())
    cutoff = (utcnow() - ORPHAN_FILE_AGE).timestamp()

    deleted = 0
    for path in folder.iterdir():
        if path.is_symlink() or not path.is_file() or path.name in known:
            continue
        if path.stat().st_mtime >= cutoff:
            continue
        if not dry_run:
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("남은 파일 삭제 실패 (%s): %s", path.name, exc)
                continue
        deleted += 1
    return deleted


def _attachment_path(storage_key: str) -> Path:
    """첨부 폴더 안의 경로만 돌려준다. 폴더 밖을 가리키는 값이면 지우지 않도록 오류."""
    folder = Path(settings.attachment_dir).resolve()
    path = (folder / storage_key).resolve()
    if path.parent != folder:
        raise OSError(f"첨부 폴더 밖의 경로입니다: {storage_key}")
    return path


def run_all(*, dry_run: bool = False) -> dict[str, int]:
    """세 가지 정리를 차례로 한다. 첨부 행을 먼저 지우므로, 그 파일 삭제가 실패해도 같은 실행의 'DB에 없는 파일' 정리에서 다시 지운다."""
    with SessionLocal() as db:
        return {
            "idempotencyKeys": delete_old_idempotency_keys(db, dry_run=dry_run),
            "unattachedAttachments": delete_unattached_attachments(db, dry_run=dry_run),
            "orphanFiles": delete_orphan_files(db, dry_run=dry_run),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="오래된 중복 방지 키와 남는 첨부 파일을 지운다.")
    parser.add_argument("--dry-run", action="store_true", help="지우지 않고 지울 개수만 보여 준다")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    counts = run_all(dry_run=args.dry_run)
    verb = "지울" if args.dry_run else "지운"
    print(f"중복 방지 키 {verb} 개수: {counts['idempotencyKeys']}")
    print(f"검토 건에 연결되지 않은 첨부 {verb} 개수: {counts['unattachedAttachments']}")
    print(f"DB에 없는 파일 {verb} 개수: {counts['orphanFiles']}")


if __name__ == "__main__":
    main()
