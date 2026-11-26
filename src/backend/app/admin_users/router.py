"""사용자·권한 관리 (관리자). API 설계서 3장 '관리자 계정 처리 트랜잭션', 5장 '관리자 목록'·'사용자 비활성화·삭제·이관'.

변경 API(수정·이관·삭제)는 각각 하나의 트랜잭션이다. 대상 users 행을 먼저 잠그고(SELECT … FOR UPDATE)
검사 → 변경 순서로 처리하며, 중간에 실패하면 전부 롤백된다.
잠금 순서는 항상 users → 업무 테이블(reviews, legal_submissions).
"""

import secrets
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.admin_users.service import create_user
from app.auth.sessions import revoke_user_sessions
from app.core.activity import log_activity
from app.core.deps import Admin, get_db
from app.core.errors import ApiError
from app.core.idempotency import IdemKey, run_idempotent
from app.core.pagination import keyset_page
from app.core.schemas import CamelModel, Text
from app.core.security import UNUSABLE_PASSWORD, is_valid_password
from app.models import (
    ActivityLog,
    Attachment,
    IdempotencyKey,
    LegalSubmission,
    MenuSeen,
    Notification,
    Review,
    Session,
    User,
)
from app.notifications.service import notify

router = APIRouter(prefix="/admin/users")

Role = Literal["ADMIN", "MARKETING", "LEGAL"]
DELETED_NAME = "삭제된 사용자"
OPERATIONS = {
    "LOGIN", "LOGOUT", "REVIEW_REQUESTED", "RA_RECHECK_REQUESTED", "SUGGESTION_RECHECKED",
    "SUGGESTION_DISMISSED", "RUN_RETRIED", "LEGAL_SENT", "REPORT_VIEWED", "LEGAL_OPINION_SENT",
    "REVIEW_CLOSED", "USER_CREATED", "USER_UPDATED", "WORK_HANDED_OVER", "USER_DELETED", "USER_ANONYMIZED",
}  # fmt: skip


# ---------- 요청 모델 ----------


class UserCreate(CamelModel):
    name: Text
    email: Text
    temporary_password: Text
    role: Role


class UserUpdate(CamelModel):
    role: Role | None = None
    status: Literal["ACTIVE", "INACTIVE", "DELETED"] | None = None  # DELETED는 받아서 422로 거절


class HandoverRequest(CamelModel):
    to_user_id: str | None = None  # 마케팅 건이 있으면 필수, 법무 건만 있으면 생략


# ---------- 공통 ----------


def admin_row(u: User) -> dict:
    return {
        "userId": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "status": u.status,
        "lastLoginAt": u.last_login_at,
    }


def lock_user(db: DbSession, user_id: str) -> User:
    """대상 사용자 행을 잠근다. 없거나 '삭제된 사용자'면 404."""
    u = db.get(User, user_id, with_for_update=True)
    if u is None or u.status == "DELETED":
        raise ApiError(404, "NOT_FOUND", "사용자를 찾을 수 없습니다.")
    return u


def protect(db: DbSession, admin: User, target: User) -> None:
    """자기 자신 403, 마지막 활성 관리자 409 LAST_ADMIN."""
    if target.id == admin.id:
        raise ApiError(403, "FORBIDDEN", "본인 계정은 비활성화·삭제하거나 역할을 바꿀 수 없습니다.")
    if target.role == "ADMIN" and target.status == "ACTIVE":
        # 다른 활성 관리자 행도 잠가서, 두 관리자가 동시에 서로를 비활성화하는 경우를 막는다.
        others = db.scalars(
            select(User.id)
            .where(User.role == "ADMIN", User.status == "ACTIVE", User.id != target.id)
            .with_for_update()
        ).all()
        if not others:
            raise ApiError(409, "LAST_ADMIN", "마지막 관리자는 비활성화·삭제하거나 역할을 바꿀 수 없습니다.")


def open_reviews(db: DbSession, user_id: str, lock: bool = False) -> list[Review]:
    """마케팅이 넘길 건: 본인이 작성했고 끝나지 않은 건 전체."""
    stmt = select(Review).where(Review.author_id == user_id, Review.closed_type.is_(None))
    return list(db.scalars(stmt.with_for_update() if lock else stmt).all())


def in_review_submissions(db: DbSession, user_id: str, lock: bool = False) -> list[LegalSubmission]:
    """법무가 넘길 건: 본인이 담당하는 검토 중(IN_REVIEW) 건."""
    stmt = select(LegalSubmission).where(
        LegalSubmission.reviewer_id == user_id, LegalSubmission.status == "IN_REVIEW"
    )
    return list(db.scalars(stmt.with_for_update() if lock else stmt).all())


def check_handover(db: DbSession, u: User) -> None:
    reviews, subs = open_reviews(db, u.id), in_review_submissions(db, u.id)
    if reviews or subs:
        raise ApiError(
            409,
            "HANDOVER_REQUIRED",
            f"다른 담당자에게 넘겨야 할 건이 {len(reviews) + len(subs)}건 있습니다. 먼저 넘겨 주세요.",
            details={"openReviews": len(reviews), "inReviewSubmissions": len(subs)},
        )


def record_counts(db: DbSession, user_id: str) -> dict:
    """기록: 보고서 작성·첨부·법무 요청·법무 검토. 활동 로그와 알림은 기록이 아니다."""

    def count(stmt) -> int:
        return db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    return {
        "reviews": count(select(Review.id).where(Review.author_id == user_id)),
        "attachments": count(select(Attachment.id).where(Attachment.uploaded_by == user_id)),
        "legalSubmissions": count(
            select(LegalSubmission.id).where(
                or_(LegalSubmission.sender_id == user_id, LegalSubmission.reviewer_id == user_id)
            )
        ),
    }


def delete_personal_data(db: DbSession, user_id: str, *, with_activity_logs: bool) -> None:
    """본인만 쓰던 데이터 삭제 (자식 테이블 먼저)."""
    if with_activity_logs:
        db.execute(delete(ActivityLog).where(ActivityLog.user_id == user_id))
    db.execute(delete(Notification).where(Notification.user_id == user_id))
    db.execute(delete(MenuSeen).where(MenuSeen.user_id == user_id))
    db.execute(delete(IdempotencyKey).where(IdempotencyKey.user_id == user_id))
    db.execute(delete(Session).where(Session.user_id == user_id))


# ---------- API ----------


@router.get("", summary="사용자 목록 (AD-1)")
def list_users(
    admin: Admin,
    db: DbSession = Depends(get_db),
    q: str | None = None,
    role: Role | None = None,
    status: Literal["ACTIVE", "INACTIVE"] | None = None,  # 삭제된 사용자는 목록·필터에 없다
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    stmt = select(User).where(User.status != "DELETED")
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.name.ilike(like), User.email.ilike(like)))
    if role:
        stmt = stmt.where(User.role == role)
    if status:
        stmt = stmt.where(User.status == status)
    rows, next_cursor = keyset_page(
        db, stmt, [User.name, User.id], limit=limit, cursor=cursor,
        filters={"q": q, "role": role, "status": status},
    )  # fmt: skip
    return {"items": [admin_row(u) for u in rows], "nextCursor": next_cursor}


@router.post("", status_code=201, summary="사용자 등록 (AD-2 → AD-5)")
def register_user(body: UserCreate, admin: Admin, db: DbSession = Depends(get_db)) -> dict:
    if not is_valid_password(body.temporary_password):
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "임시 비밀번호는 8자 이상, 영문·숫자를 포함해 주세요.",
            field_errors=[{"field": "temporaryPassword", "code": "INVALID"}],
        )
    u = create_user(
        db, name=body.name, email=body.email, role=body.role, password=body.temporary_password,
        must_change_password=True,
    )  # fmt: skip
    log_activity(db, admin.id, "USER_CREATED", u.id)  # 사용자 관리 로그 대상은 userId
    db.commit()
    return admin_row(u)


@router.patch("/{userId}", summary="역할·상태 변경 (AD-6 → AD-7)")
def update_user(userId: str, body: UserUpdate, admin: Admin, db: DbSession = Depends(get_db)) -> dict:
    if body.status == "DELETED":
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "계정 삭제는 [삭제]로 처리해 주세요.",
            field_errors=[{"field": "status", "code": "INVALID"}],
        )
    u = lock_user(db, userId)
    deactivate = body.status == "INACTIVE" and u.status != "INACTIVE"
    role_change = body.role is not None and body.role != u.role
    if deactivate or role_change:
        protect(db, admin, u)
        check_handover(db, u)
    if body.role:
        u.role = body.role
    if body.status:
        u.status = body.status
    if deactivate or role_change:
        revoke_user_sessions(db, u.id)  # 바로 로그아웃
    log_activity(db, admin.id, "USER_UPDATED", u.id)
    db.commit()
    return admin_row(u)


@router.post("/{userId}/handover", summary="담당 건 이관 [넘기기]")
def handover(
    userId: str,
    body: HandoverRequest,
    admin: Admin,
    db: DbSession = Depends(get_db),
    idempotency_key: IdemKey = None,
):
    def work() -> tuple[int, dict]:
        u = lock_user(db, userId)
        to = None
        reviews = open_reviews(db, u.id)
        if reviews:
            to = db.get(User, body.to_user_id, with_for_update=True) if body.to_user_id else None
            if to is None or to.status != "ACTIVE" or to.role != "MARKETING" or to.id == u.id:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "넘겨받을 마케팅 담당자를 선택해 주세요.",
                    field_errors=[{"field": "toUserId", "code": "INVALID" if body.to_user_id else "REQUIRED"}],
                )
        # users 잠금이 끝난 뒤 업무 테이블 잠금
        reviews = open_reviews(db, u.id, lock=True)
        subs = in_review_submissions(db, u.id, lock=True)

        if reviews:
            ids = [r.id for r in reviews]
            db.execute(update(Review).where(Review.id.in_(ids)).values(author_id=to.id))
            # 진행 중 법무 요청의 보낸 사람도 바꿔, 검토 의견 알림이 받는 사람에게 가게 한다
            db.execute(
                update(LegalSubmission)
                .where(LegalSubmission.review_id.in_(ids), LegalSubmission.status != "OPINION_SENT")
                .values(sender_id=to.id)
            )
            notify(db, to.id, "WORK_HANDED_OVER", f"담당 건 {len(reviews)}건을 넘겨받았습니다.", menu="INBOX")

        if subs:
            legal_ids = db.scalars(
                select(User.id).where(User.role == "LEGAL", User.status == "ACTIVE", User.id != u.id)
            ).all()
            for s in subs:
                s.status, s.reviewer_id, s.started_at = "PENDING", None, None
                title = db.scalar(select(Review.title).where(Review.id == s.review_id))
                for lid in legal_ids:
                    notify(
                        db, lid, "LEGAL_REASSIGN_NEEDED", f"{title} · 담당자 재지정이 필요합니다.",
                        review_id=s.review_id, submission_id=s.id, menu="INBOX",
                    )  # fmt: skip

        if reviews or subs:
            log_activity(db, admin.id, "WORK_HANDED_OVER", u.id)
        return 200, {"handedOverReviews": len(reviews), "releasedSubmissions": len(subs)}

    payload = {"userId": userId, **body.model_dump(by_alias=True)}
    return run_idempotent(db, admin.id, idempotency_key, payload, work)


@router.delete("/{userId}", status_code=204, summary="계정 삭제 [삭제]")
def delete_user(
    userId: str,
    admin: Admin,
    db: DbSession = Depends(get_db),
    mode: Literal["anonymize"] | None = None,
):
    u = lock_user(db, userId)
    protect(db, admin, u)
    check_handover(db, u)
    records = record_counts(db, u.id)

    if not any(records.values()):
        # 기록 없음: 딸린 데이터와 계정 행 삭제
        delete_personal_data(db, u.id, with_activity_logs=True)
        db.delete(u)
        log_activity(db, admin.id, "USER_DELETED", userId)
        try:
            db.commit()
        except IntegrityError:
            # 검사 뒤 기록이 생겨 외래키 오류가 나도 USER_HAS_RECORDS로 돌려준다
            db.rollback()
            raise ApiError(409, "USER_HAS_RECORDS", _HAS_RECORDS_MSG, details=record_counts(db, userId))
        return Response(status_code=204)

    if mode != "anonymize":
        raise ApiError(409, "USER_HAS_RECORDS", _HAS_RECORDS_MSG, details=records)

    # '삭제된 사용자'로 변경: 개인정보만 지우고 userId만 남긴다. 보고서·법무 기록·활동 로그는 남긴다.
    u.name = DELETED_NAME
    u.email = f"deleted+{u.id}@invalid"
    u.password_hash = UNUSABLE_PASSWORD + secrets.token_hex(16)  # 로그인할 수 없는 값 (NOT NULL)
    u.last_login_at = None
    u.status = "DELETED"
    delete_personal_data(db, u.id, with_activity_logs=False)
    log_activity(db, admin.id, "USER_ANONYMIZED", u.id)
    db.commit()
    return JSONResponse(jsonable_encoder(admin_row(u)), status_code=200)


_HAS_RECORDS_MSG = (
    "보고서 생성 기록이 있어 비활성화로 변경 부탁드립니다. 그래도 삭제하시겠습니까? 개인정보가 지워지며 되돌릴 수 없습니다."
)


@router.get("/{userId}/activity", summary="사용자 활동 로그 (AD-10~AD-17)")
def activity(
    userId: str,
    admin: Admin,
    db: DbSession = Depends(get_db),
    operation: str | None = None,  # 콤마 구분. 로그인·로그아웃 필터 = LOGIN,LOGOUT
    from_: Annotated[datetime | None, Query(alias="from")] = None,  # 포함
    to: datetime | None = None,  # 미포함
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    u = db.get(User, userId)
    if u is None or u.status == "DELETED":
        raise ApiError(404, "NOT_FOUND", "사용자를 찾을 수 없습니다.")
    ops = sorted(set(operation.split(","))) if operation else []
    if not set(ops) <= OPERATIONS:
        raise ApiError(400, "INVALID_QUERY", "작업 종류를 확인해 주세요.")

    stmt = select(ActivityLog).where(ActivityLog.user_id == userId)
    if ops:
        stmt = stmt.where(ActivityLog.operation.in_(ops))
    if from_:
        stmt = stmt.where(ActivityLog.occurred_at >= from_)
    if to:
        stmt = stmt.where(ActivityLog.occurred_at < to)
    rows, next_cursor = keyset_page(
        db, stmt, [ActivityLog.occurred_at, ActivityLog.id], limit=limit, cursor=cursor,
        filters={"user": userId, "ops": ops, "from": from_, "to": to}, desc=True,
    )  # fmt: skip
    return {
        "user": admin_row(u),
        "items": [
            {"activityId": a.id, "operation": a.operation, "targetLabel": a.target_label, "occurredAt": a.occurred_at}
            for a in rows
        ],
        "nextCursor": next_cursor,
    }

