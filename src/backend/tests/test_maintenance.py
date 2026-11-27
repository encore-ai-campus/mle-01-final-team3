"""정리 명령 (app/maintenance.py): 오래된 중복 방지 키, 검토 건에 연결되지 않은 첨부, DB에 없는 파일."""

import os
import time
from datetime import timedelta

import pytest
from sqlalchemy import select, update

from app import maintenance
from app.core.config import settings
from app.core.db import SessionLocal
from app.models import Attachment, IdempotencyKey
from tests.helpers import API

BODY = {"title": "면역력 강화 음료 광고", "productCategory": "GENERAL_FOOD", "channel": "DETAIL_PAGE", "text": "하루 한 포"}


@pytest.fixture
def att_dir(tmp_path, monkeypatch):
    """이 테스트만 쓰는 빈 첨부 폴더."""
    monkeypatch.setattr(settings, "attachment_dir", tmp_path)
    return tmp_path


def upload(c) -> str:
    r = c.post(f"{API}/attachments", files={"file": ("근거자료.pdf", b"%PDF-1.4 test")}, data={"purpose": "AD_COPY"})
    assert r.status_code == 201, r.text
    return r.json()["attachmentId"]


def file_of(att_id: str):
    with SessionLocal() as db:
        return settings.attachment_dir / db.get(Attachment, att_id).storage_key


def age_attachment(att_id: str, hours: int = 25) -> None:
    with SessionLocal() as db:
        db.execute(
            update(Attachment)
            .where(Attachment.id == att_id)
            .values(created_at=Attachment.created_at - timedelta(hours=hours))
        )
        db.commit()


def age_key(key: str, hours: int = 25) -> None:
    with SessionLocal() as db:
        db.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.key == key)
            .values(created_at=IdempotencyKey.created_at - timedelta(hours=hours))
        )
        db.commit()


def age_file(path, hours: int = 2) -> None:
    t = time.time() - hours * 3600
    os.utime(path, (t, t))


def keys() -> set[str]:
    with SessionLocal() as db:
        return set(db.scalars(select(IdempotencyKey.key)))


def attachment_ids() -> set[str]:
    with SessionLocal() as db:
        return set(db.scalars(select(Attachment.id)))


# ---------- 중복 방지 키 ----------


def test_idempotency_keys_older_than_24h_are_deleted(mkt):
    first = mkt.post(f"{API}/reviews", json=BODY, headers={"Idempotency-Key": "k-old"})
    mkt.post(f"{API}/reviews", json=BODY, headers={"Idempotency-Key": "k-new"})
    age_key("k-old")

    with SessionLocal() as db:
        assert maintenance.delete_old_idempotency_keys(db) == 1
    assert keys() == {"k-new"}

    # 지운 키는 새 요청으로 처리된다 (24시간이 지난 재전송)
    again = mkt.post(f"{API}/reviews", json=BODY, headers={"Idempotency-Key": "k-old"})
    assert again.status_code == 202 and again.json()["reviewId"] != first.json()["reviewId"]


# ---------- 검토 건에 연결되지 않은 첨부 ----------


def test_unattached_attachment_deleted_after_24h(mkt, att_dir):
    old_unattached = upload(mkt)
    new_unattached = upload(mkt)
    old_attached = upload(mkt)
    assert mkt.post(f"{API}/reviews", json={**BODY, "attachmentIds": [old_attached]}).status_code == 202
    old_file = file_of(old_unattached)
    age_attachment(old_unattached)
    age_attachment(old_attached)

    with SessionLocal() as db:
        assert maintenance.delete_unattached_attachments(db) == 1

    assert attachment_ids() == {new_unattached, old_attached}  # 최근 파일·검토 건에 붙은 파일은 남는다
    assert not old_file.exists()
    assert file_of(new_unattached).exists() and file_of(old_attached).exists()

    # 지운 첨부로 검토를 요청하면 지금처럼 422 (다시 올려 달라는 안내)
    r = mkt.post(f"{API}/reviews", json={**BODY, "attachmentIds": [old_unattached]})
    assert r.status_code == 422 and r.json()["error"]["fieldErrors"] == [{"field": "attachmentIds[0]", "code": "INVALID"}]


# ---------- DB에 없는 파일 ----------


def test_orphan_files_older_than_1h_are_deleted(mkt, att_dir):
    kept = upload(mkt)
    age_file(file_of(kept))  # DB 행이 있으면 오래돼도 남는다
    old_orphan = att_dir / "att_ghost.pdf"
    old_orphan.write_bytes(b"%PDF-1.4 leftover")
    age_file(old_orphan)
    new_orphan = att_dir / "att_uploading.pdf"  # 올리는 중일 수 있는 파일
    new_orphan.write_bytes(b"%PDF-1.4 new")
    (att_dir / "sub").mkdir()  # 폴더는 건드리지 않는다

    with SessionLocal() as db:
        assert maintenance.delete_orphan_files(db) == 1

    assert not old_orphan.exists()
    assert new_orphan.exists() and file_of(kept).exists() and (att_dir / "sub").is_dir()


def test_missing_attachment_folder_is_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "attachment_dir", tmp_path / "none")
    with SessionLocal() as db:
        assert maintenance.delete_orphan_files(db) == 0


def test_attachment_path_outside_folder_is_refused(att_dir):
    with pytest.raises(OSError):
        maintenance._attachment_path("../outside.pdf")


# ---------- 명령 전체 ----------


def test_dry_run_deletes_nothing_then_run_deletes(mkt, att_dir):
    mkt.post(f"{API}/reviews", json=BODY, headers={"Idempotency-Key": "k-old"})
    age_key("k-old")
    att = upload(mkt)
    age_attachment(att)
    orphan = att_dir / "att_ghost.pdf"
    orphan.write_bytes(b"%PDF-1.4 leftover")
    age_file(orphan)

    expected = {"idempotencyKeys": 1, "unattachedAttachments": 1, "orphanFiles": 1}
    assert maintenance.run_all(dry_run=True) == expected
    assert keys() == {"k-old"} and attachment_ids() == {att} and orphan.exists()  # 아무것도 지우지 않음

    assert maintenance.run_all() == expected
    assert keys() == set() and attachment_ids() == set() and not orphan.exists()
    assert list(att_dir.iterdir()) == []

    assert maintenance.run_all() == {"idempotencyKeys": 0, "unattachedAttachments": 0, "orphanFiles": 0}
