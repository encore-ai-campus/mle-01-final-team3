"""DB 테이블 정의. 기준: ERD_v0.4.dbml

- 테이블을 바꾸려면 이 파일을 고친 뒤 새 마이그레이션을 만든다 (README 참고).
- 시각은 모두 timezone 포함(timestamptz)으로 저장한다.
- 코드 값(역할, 상태 등)은 varchar 문자열로 저장한다.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

ID = String(32)
CODE = String(32)
TS = DateTime(timezone=True)


class User(Base):
    """사용자. 삭제 2가지: 기록 없으면 행 삭제, 기록 있으면 개인정보만 덮어씀(status=DELETED)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(ID, primary_key=True)  # 예: usr_001
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)  # 로그인 아이디
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(CODE)  # MARKETING, LEGAL, ADMIN
    status: Mapped[str] = mapped_column(CODE, server_default="ACTIVE")  # ACTIVE, INACTIVE, DELETED
    must_change_password: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(TS)
    created_at: Mapped[datetime | None] = mapped_column(TS)


class Review(Base):
    """광고 검토 건."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(ID, primary_key=True)  # 예: revw_001
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    product_category: Mapped[str] = mapped_column(CODE)  # HEALTH_FUNCTIONAL_FOOD, GENERAL_FOOD, CHILDREN_PREFERRED_FOOD
    text: Mapped[str] = mapped_column(Text)  # 처음 입력한 원문
    closed_type: Mapped[str | None] = mapped_column(CODE)  # ENDED, PUBLISHED, CANCELED
    closed_at: Mapped[datetime | None] = mapped_column(TS)
    created_at: Mapped[datetime | None] = mapped_column(TS)
    updated_at: Mapped[datetime | None] = mapped_column(TS)


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))  # pdf, xlsx, docx
    size: Mapped[int] = mapped_column(Integer)  # 바이트. 제출당 합계 10MB 이하
    storage_key: Mapped[str] = mapped_column(String(255))
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime | None] = mapped_column(TS)


class ReviewAttachment(Base):
    __tablename__ = "review_attachments"
    __table_args__ = (PrimaryKeyConstraint("review_id", "attachment_id"),)

    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"))
    attachment_id: Mapped[str] = mapped_column(ForeignKey("attachments.id"))


class ReviewRun(Base):
    """실행 1번. 재시도는 최초 실행별 최대 2회."""

    __tablename__ = "review_runs"

    id: Mapped[str] = mapped_column(ID, primary_key=True)  # 예: run_001
    review_id: Mapped[str | None] = mapped_column(ForeignKey("reviews.id"))
    stage: Mapped[str] = mapped_column(CODE)  # AI_SCREENING, RA_SUGGEST, RA_RECHECK
    status: Mapped[str] = mapped_column(CODE)  # QUEUED, RUNNING, SUCCEEDED, FAILED
    attempt: Mapped[int | None] = mapped_column(Integer, server_default=text("1"))
    retry_of: Mapped[str | None] = mapped_column(ForeignKey("review_runs.id"))
    error_code: Mapped[str | None] = mapped_column(String(50))  # 예: RUN_TIMEOUT
    error_message: Mapped[str | None] = mapped_column(String(500))
    error_retryable: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime | None] = mapped_column(TS)
    updated_at: Mapped[datetime | None] = mapped_column(TS)
    started_at: Mapped[datetime | None] = mapped_column(TS)
    finished_at: Mapped[datetime | None] = mapped_column(TS)
    suggestion: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # RA_SUGGEST만 {text, rationale, status}


class Report(Base):
    """보고서. 실행 1번 = 보고서 1개. 재심의마다 version이 오름."""

    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("review_id", "version"),)

    run_id: Mapped[str] = mapped_column(ForeignKey("review_runs.id"), primary_key=True)
    review_id: Mapped[str | None] = mapped_column(ForeignKey("reviews.id"))
    stage: Mapped[str] = mapped_column(CODE)  # AI_SCREENING, RA_RECHECK
    version: Mapped[int] = mapped_column(Integer)
    reviewed_text: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(CODE)  # SUITABLE, UNSUITABLE
    summary: Mapped[str] = mapped_column(Text)
    improvement_note: Mapped[str | None] = mapped_column(Text)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime | None] = mapped_column(TS)


class LegalSubmission(Base):
    """법무 검토 요청 건."""

    __tablename__ = "legal_submissions"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    review_id: Mapped[str | None] = mapped_column(ForeignKey("reviews.id"))
    report_run_id: Mapped[str | None] = mapped_column(ForeignKey("reports.run_id"), unique=True)
    sender_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(CODE)  # PENDING, IN_REVIEW, OPINION_SENT
    reason: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(TS)
    started_at: Mapped[datetime | None] = mapped_column(TS)
    decided_at: Mapped[datetime | None] = mapped_column(TS)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(CODE)
    message: Mapped[str] = mapped_column(String(500))
    review_id: Mapped[str | None] = mapped_column(ID)  # ERD에 외래키 없음
    submission_id: Mapped[str | None] = mapped_column(ID)  # ERD에 외래키 없음
    menu: Mapped[str | None] = mapped_column(CODE)  # INBOX, SENT_LIST
    created_at: Mapped[datetime | None] = mapped_column(TS)
    read_at: Mapped[datetime | None] = mapped_column(TS)


class MenuSeen(Base):
    __tablename__ = "menu_seen"
    __table_args__ = (PrimaryKeyConstraint("user_id", "menu"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    menu: Mapped[str] = mapped_column(CODE)
    seen_at: Mapped[datetime | None] = mapped_column(TS)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    operation: Mapped[str] = mapped_column(CODE)
    target_label: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(TS)


class Session(Base):
    """로그인 세션. 로그인 1번 = 행 1개. 만료는 로그인 시점 + 10시간 고정."""

    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)  # 쿠키 값의 SHA-256
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(TS)
    expires_at: Mapped[datetime] = mapped_column(TS, index=True)


class IdempotencyKey(Base):
    """중복 요청 방지 키."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (PrimaryKeyConstraint("user_id", "key"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    status_code: Mapped[int | None] = mapped_column(Integer)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime | None] = mapped_column(TS)
