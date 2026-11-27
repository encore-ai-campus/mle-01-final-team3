"""7단계: 관리자 사용자 관리 API. 검토 흐름 및 Agent 연동 담당의 샘플 테스트 J1~J5를 우리 DB 구조로 옮긴 것 포함."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_users.router import protect
from app.admin_users.service import create_user
from app.core.errors import ApiError
from app.core.ids import new_id
from app.core.security import utcnow
from app.main import app
from app.models import ActivityLog, IdempotencyKey, LegalSubmission, Notification, Review, Session, User

API = "/api/v1"
PW = "password123"


def make_user(db, email, role="MARKETING", status="ACTIVE"):
    u = create_user(db, name=email.split("@")[0], email=email, role=role, password=PW, must_change_password=False)
    u.status = status
    db.commit()
    return u


def client_for(email, login_type="STAFF") -> TestClient:
    c = TestClient(app)
    res = c.post(f"{API}/auth/login", json={"email": email, "password": PW, "loginType": login_type})
    assert res.status_code == 200, res.text
    return c


def make_review(db, author_id, title="광고", closed=False):
    r = Review(
        id=new_id(db, "revw"), author_id=author_id, title=title, product_category="GENERAL_FOOD",
        channel="DETAIL_PAGE", text="문구", closed_type="ENDED" if closed else None, created_at=utcnow(),
    )  # fmt: skip
    db.add(r)
    db.commit()
    return r


def make_submission(db, review, sender_id, reviewer_id=None, status="PENDING"):
    s = LegalSubmission(
        id=new_id(db, "sub"), review_id=review.id, sender_id=sender_id, reviewer_id=reviewer_id,
        status=status, sent_at=utcnow(),
    )  # fmt: skip
    db.add(s)
    db.commit()
    return s


def err(res, status, code):
    assert res.status_code == status, res.text
    assert res.json()["error"]["code"] == code
    return res.json()["error"]


@pytest.fixture
def admin(db):
    make_user(db, "admin@test.com", role="ADMIN")
    return client_for("admin@test.com", "ADMIN")


def admin_id(db):
    return db.scalar(select(User.id).where(User.email == "admin@test.com"))


# ---------- 권한 ----------


def test_non_admin_is_forbidden(db):
    make_user(db, "m@test.com")
    err(client_for("m@test.com").get(f"{API}/admin/users"), 403, "FORBIDDEN")


# ---------- 목록 ----------


def test_list_filters_and_hides_deleted(db, admin):
    make_user(db, "kim@test.com")
    make_user(db, "lee@test.com", role="LEGAL", status="INACTIVE")
    make_user(db, "gone@test.com", status="DELETED")

    emails = [u["email"] for u in admin.get(f"{API}/admin/users").json()["items"]]
    assert "gone@test.com" not in emails and len(emails) == 3
    assert [u["email"] for u in admin.get(f"{API}/admin/users", params={"q": "kim"}).json()["items"]] == ["kim@test.com"]
    assert [u["role"] for u in admin.get(f"{API}/admin/users", params={"role": "LEGAL"}).json()["items"]] == ["LEGAL"]
    assert [u["status"] for u in admin.get(f"{API}/admin/users", params={"status": "INACTIVE"}).json()["items"]] == ["INACTIVE"]
    err(admin.get(f"{API}/admin/users", params={"status": "DELETED"}), 400, "INVALID_QUERY")

    row = admin.get(f"{API}/admin/users", params={"q": "kim"}).json()["items"][0]
    assert set(row) == {"userId", "name", "email", "role", "status", "lastLoginAt"}


def test_list_cursor_paging(db, admin):
    for i in range(3):
        make_user(db, f"u{i}@test.com")
    seen, cursor = [], None
    while True:
        page = admin.get(f"{API}/admin/users", params={"limit": 2, **({"cursor": cursor} if cursor else {})}).json()
        seen += [u["userId"] for u in page["items"]]
        cursor = page["nextCursor"]
        if not cursor:
            break
    assert len(seen) == 4 and len(set(seen)) == 4  # 관리자 포함 4명, 중복 없음

    first = admin.get(f"{API}/admin/users", params={"limit": 1}).json()
    err(admin.get(f"{API}/admin/users", params={"limit": 1, "cursor": first["nextCursor"], "q": "u"}), 400, "INVALID_CURSOR")
    err(admin.get(f"{API}/admin/users", params={"cursor": "엉터리"}), 400, "INVALID_CURSOR")


# ---------- 등록 ----------


def test_register_user_then_first_login(db, admin):
    res = admin.post(f"{API}/admin/users", json={"name": "새사람", "email": "new@test.com", "temporaryPassword": "temp1234", "role": "LEGAL"})
    assert res.status_code == 201
    row = res.json()
    assert row["role"] == "LEGAL" and row["status"] == "ACTIVE" and row["userId"].startswith("usr_")

    login = TestClient(app).post(f"{API}/auth/login", json={"email": "new@test.com", "password": "temp1234"})
    assert login.json()["mustChangePassword"] is True
    log = db.scalar(select(ActivityLog).where(ActivityLog.operation == "USER_CREATED"))
    assert log.user_id == admin_id(db) and log.target_label == row["userId"]


def test_register_errors(db, admin):
    make_user(db, "dup@test.com")
    body = {"name": "x", "email": "dup@test.com", "temporaryPassword": "temp1234", "role": "MARKETING"}
    err(admin.post(f"{API}/admin/users", json=body), 409, "EMAIL_ALREADY_EXISTS")

    e = err(admin.post(f"{API}/admin/users", json={"name": "x", "email": "a@test.com", "role": "MARKETING"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "temporaryPassword", "code": "REQUIRED"}]
    e = err(admin.post(f"{API}/admin/users", json={**body, "email": "b@test.com", "temporaryPassword": "short"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "temporaryPassword", "code": "INVALID"}]


# ---------- 수정 (J1) ----------


def test_self_protection_and_deleted_status(db, admin):
    me = admin_id(db)
    err(admin.patch(f"{API}/admin/users/{me}", json={"status": "INACTIVE"}), 403, "FORBIDDEN")
    err(admin.patch(f"{API}/admin/users/{me}", json={"role": "LEGAL"}), 403, "FORBIDDEN")
    err(admin.delete(f"{API}/admin/users/{me}"), 403, "FORBIDDEN")
    m = make_user(db, "m@test.com")
    e = err(admin.patch(f"{API}/admin/users/{m.id}", json={"status": "DELETED"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "status", "code": "INVALID"}]
    err(admin.patch(f"{API}/admin/users/usr_없음", json={"status": "INACTIVE"}), 404, "NOT_FOUND")


def test_last_admin_rule(db):
    """API로는 호출한 관리자 자신이 활성 관리자라 마지막 관리자 상황이 잘 안 생긴다. 검사 함수를 직접 확인한다."""
    only = make_user(db, "only@test.com", role="ADMIN")
    other = make_user(db, "other@test.com", role="ADMIN", status="INACTIVE")
    with pytest.raises(ApiError) as e:
        protect(db, other, db.get(User, only.id))
    assert e.value.code == "LAST_ADMIN"


def test_deactivate_revokes_sessions(db, admin):
    m = make_user(db, "m@test.com")
    mc = client_for("m@test.com")
    res = admin.patch(f"{API}/admin/users/{m.id}", json={"status": "INACTIVE"})
    assert res.status_code == 200 and res.json()["status"] == "INACTIVE"
    assert mc.get(f"{API}/me").status_code == 401
    err(TestClient(app).post(f"{API}/auth/login", json={"email": "m@test.com", "password": PW}), 403, "ACCOUNT_INACTIVE")

    assert admin.patch(f"{API}/admin/users/{m.id}", json={"status": "ACTIVE"}).json()["status"] == "ACTIVE"  # 다시 활성화


def test_role_change_revokes_sessions(db, admin):
    m = make_user(db, "m@test.com")
    mc = client_for("m@test.com")
    assert admin.patch(f"{API}/admin/users/{m.id}", json={"role": "LEGAL"}).json()["role"] == "LEGAL"
    assert mc.get(f"{API}/me").status_code == 401


# ---------- 이관 (J2·J3) ----------


def test_marketing_handover_then_deactivate(db, admin):
    giver, taker, legal = make_user(db, "giver@test.com"), make_user(db, "taker@test.com"), make_user(db, "l@test.com", role="LEGAL")
    r1, r2 = make_review(db, giver.id, "광고1"), make_review(db, giver.id, "광고2")
    make_review(db, giver.id, "끝난 광고", closed=True)
    sub = make_submission(db, r2, giver.id)

    e = err(admin.patch(f"{API}/admin/users/{giver.id}", json={"status": "INACTIVE"}), 409, "HANDOVER_REQUIRED")
    assert e["details"] == {"openReviews": 2, "inReviewSubmissions": 0}

    e = err(admin.post(f"{API}/admin/users/{giver.id}/handover", json={}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "toUserId", "code": "REQUIRED"}]
    for bad in (legal.id, giver.id, "usr_없음"):
        e = err(admin.post(f"{API}/admin/users/{giver.id}/handover", json={"toUserId": bad}), 422, "VALIDATION_ERROR")
        assert e["fieldErrors"] == [{"field": "toUserId", "code": "INVALID"}]

    res = admin.post(f"{API}/admin/users/{giver.id}/handover", json={"toUserId": taker.id}, headers={"Idempotency-Key": "j2"})
    assert res.status_code == 200 and res.json() == {"handedOverReviews": 2, "releasedSubmissions": 0}

    db.expire_all()
    assert db.get(Review, r1.id).author_id == taker.id
    assert db.get(LegalSubmission, sub.id).sender_id == taker.id
    note = db.scalar(select(Notification).where(Notification.user_id == taker.id))
    assert note.type == "WORK_HANDED_OVER" and note.message == "담당 건 2건을 넘겨받았습니다."

    assert admin.patch(f"{API}/admin/users/{giver.id}", json={"status": "INACTIVE"}).status_code == 200


def test_handover_idempotency(db, admin):
    giver, taker = make_user(db, "giver@test.com"), make_user(db, "taker@test.com")
    make_review(db, giver.id)
    url, h = f"{API}/admin/users/{giver.id}/handover", {"Idempotency-Key": "same-key"}

    first = admin.post(url, json={"toUserId": taker.id}, headers=h)
    again = admin.post(url, json={"toUserId": taker.id}, headers=h)  # 응답 못 받아서 다시 보냄
    assert first.json() == again.json() == {"handedOverReviews": 1, "releasedSubmissions": 0}
    assert len(db.scalars(select(Notification).where(Notification.user_id == taker.id)).all()) == 1  # 한 번만 처리

    other = make_user(db, "other@test.com")
    err(admin.post(url, json={"toUserId": other.id}, headers=h), 409, "STATE_CONFLICT")  # 같은 키 + 다른 내용


def test_legal_handover_returns_to_pending(db, admin):
    mkt = make_user(db, "m@test.com")
    lawyer, other_lawyer = make_user(db, "l1@test.com", role="LEGAL"), make_user(db, "l2@test.com", role="LEGAL")
    review = make_review(db, mkt.id, "면역 음료")
    sub = make_submission(db, review, mkt.id, reviewer_id=lawyer.id, status="IN_REVIEW")

    err(admin.delete(f"{API}/admin/users/{lawyer.id}"), 409, "HANDOVER_REQUIRED")
    res = admin.post(f"{API}/admin/users/{lawyer.id}/handover", json={})  # 법무 건만 있으면 toUserId 생략
    assert res.json() == {"handedOverReviews": 0, "releasedSubmissions": 1}

    db.expire_all()
    s = db.get(LegalSubmission, sub.id)
    assert (s.status, s.reviewer_id, s.started_at) == ("PENDING", None, None)
    notes = db.scalars(select(Notification).where(Notification.type == "LEGAL_REASSIGN_NEEDED")).all()
    assert [(n.user_id, n.message) for n in notes] == [(other_lawyer.id, "면역 음료 · 담당자 재지정이 필요합니다.")]


# ---------- 삭제 (J4·J5) ----------


def test_delete_user_without_records(db, admin):
    """잘못 만든 계정처럼 기록이 없어도 행은 지우지 않고 '삭제된 사용자'로 바꾼다."""
    uid = make_user(db, "oops@test.com").id
    client_for("oops@test.com")  # 로그인 기록·세션
    assert admin.delete(f"{API}/admin/users/{uid}").status_code == 204

    db.expire_all()
    row = db.get(User, uid)
    assert row.name == "삭제된 사용자" and row.email == f"deleted+{uid}@invalid" and row.status == "DELETED"
    assert db.scalar(select(Session).where(Session.user_id == uid)) is None
    assert db.scalar(select(ActivityLog).where(ActivityLog.user_id == uid, ActivityLog.operation == "LOGIN"))  # 활동 로그는 남긴다
    assert db.scalar(select(ActivityLog.target_label).where(ActivityLog.operation == "USER_DELETED")) == uid
    err(admin.get(f"{API}/admin/users/{uid}/activity"), 404, "NOT_FOUND")


def test_delete_user_with_records(db, admin):
    u = make_user(db, "left@test.com")
    review = make_review(db, u.id, closed=True)

    client_for("left@test.com")  # 로그인 기록·세션
    # 기록이 있어도 막지 않고 한 번에 삭제 (개인정보만 지움)
    assert admin.delete(f"{API}/admin/users/{u.id}").status_code == 204

    db.expire_all()
    row = db.get(User, u.id)
    assert row.name == "삭제된 사용자" and row.email == f"deleted+{u.id}@invalid"
    assert row.status == "DELETED" and row.last_login_at is None
    assert db.scalar(select(Session).where(Session.user_id == u.id)) is None
    assert db.scalar(select(ActivityLog.target_label).where(ActivityLog.operation == "USER_DELETED")) == u.id
    assert db.get(Review, review.id).author_id == u.id  # 보고서 기록은 남는다
    err(TestClient(app).post(f"{API}/auth/login", json={"email": "left@test.com", "password": PW}), 401, "USER_NOT_FOUND")
    assert u.id not in [x["userId"] for x in admin.get(f"{API}/admin/users", params={"limit": 100}).json()["items"]]
    err(admin.patch(f"{API}/admin/users/{u.id}", json={"status": "ACTIVE"}), 404, "NOT_FOUND")
    err(admin.post(f"{API}/admin/users/{u.id}/handover", json={}), 404, "NOT_FOUND")
    err(admin.delete(f"{API}/admin/users/{u.id}"), 404, "NOT_FOUND")
    err(admin.get(f"{API}/admin/users/{u.id}/activity"), 404, "NOT_FOUND")
    # 같은 이메일로 다시 등록 가능
    body = {"name": "재입사", "email": "left@test.com", "temporaryPassword": "temp1234", "role": "MARKETING"}
    assert admin.post(f"{API}/admin/users", json=body).status_code == 201


# ---------- 롤백: 처리 중 오류가 나면 아무것도 바뀌지 않는다 (설계서 3장 '관리자 계정 처리 트랜잭션') ----------


@pytest.fixture
def broken_admin(admin, monkeypatch):
    """마지막 단계(활동 로그 기록)에서 일부러 오류가 나는 관리자 브라우저.

    활동 로그는 각 작업에서 저장(commit) 바로 전에 남긴다. 그래서 앞의 변경이 다 끝난 뒤 실패하는 상황이 된다.
    """
    from app.admin_users import router as admin_router

    def boom(*args, **kwargs):
        raise RuntimeError("일부러 낸 오류")

    monkeypatch.setattr(admin_router, "log_activity", boom)
    c = TestClient(app, raise_server_exceptions=False)  # 오류를 테스트로 던지지 않고 500 응답으로 받는다
    c.cookies.update(admin.cookies)
    return c


def test_register_rolls_back_on_error(db, broken_admin):
    body = {"name": "새 사용자", "email": "new@test.com", "temporaryPassword": "temp1234", "role": "MARKETING"}
    err(broken_admin.post(f"{API}/admin/users", json=body), 500, "INTERNAL_ERROR")
    db.expire_all()
    assert db.scalar(select(User).where(User.email == "new@test.com")) is None  # 계정이 만들어지지 않음


def test_update_rolls_back_on_error(db, broken_admin):
    u = make_user(db, "m@test.com")
    client_for("m@test.com")  # 로그인 세션 1개
    for body in ({"status": "INACTIVE"}, {"role": "LEGAL"}):
        err(broken_admin.patch(f"{API}/admin/users/{u.id}", json=body), 500, "INTERNAL_ERROR")
        db.expire_all()
        row = db.get(User, u.id)
        assert (row.status, row.role) == ("ACTIVE", "MARKETING"), body  # 상태·역할 그대로
        assert db.scalar(select(Session).where(Session.user_id == u.id)), body  # 세션도 그대로 (로그아웃 안 됨)


def test_handover_rolls_back_on_error(db, admin, broken_admin, monkeypatch):
    giver, taker = make_user(db, "giver@test.com"), make_user(db, "taker@test.com")
    r1, r2 = make_review(db, giver.id, "광고1"), make_review(db, giver.id, "광고2")
    sub = make_submission(db, r2, giver.id)
    url, body, h = f"{API}/admin/users/{giver.id}/handover", {"toUserId": taker.id}, {"Idempotency-Key": "k1"}

    err(broken_admin.post(url, json=body, headers=h), 500, "INTERNAL_ERROR")
    db.expire_all()
    assert db.get(Review, r1.id).author_id == db.get(Review, r2.id).author_id == giver.id  # 일부 건만 넘어가지 않음
    assert db.get(LegalSubmission, sub.id).sender_id == giver.id
    assert db.scalar(select(Notification).where(Notification.user_id == taker.id)) is None  # 알림도 없음
    assert db.scalar(select(IdempotencyKey)) is None  # 중복 방지 키도 저장되지 않음

    # 오류가 사라진 뒤 같은 키로 다시 보내면 정상 처리된다 (실패한 응답이 저장되지 않았으므로)
    monkeypatch.undo()
    res = admin.post(url, json=body, headers=h)
    assert res.status_code == 200 and res.json() == {"handedOverReviews": 2, "releasedSubmissions": 0}


def test_legal_handover_rolls_back_on_error(db, broken_admin):
    mkt, lawyer = make_user(db, "m@test.com"), make_user(db, "l1@test.com", role="LEGAL")
    make_user(db, "l2@test.com", role="LEGAL")
    sub = make_submission(db, make_review(db, mkt.id), mkt.id, reviewer_id=lawyer.id, status="IN_REVIEW")

    err(broken_admin.post(f"{API}/admin/users/{lawyer.id}/handover", json={}), 500, "INTERNAL_ERROR")
    db.expire_all()
    s = db.get(LegalSubmission, sub.id)
    assert (s.status, s.reviewer_id) == ("IN_REVIEW", lawyer.id)  # 검토 대기로 돌아가지 않음
    assert db.scalar(select(Notification).where(Notification.type == "LEGAL_REASSIGN_NEEDED")) is None


def test_delete_rolls_back_on_error(db, broken_admin):
    u = make_user(db, "left@test.com")
    make_review(db, u.id, closed=True)
    client_for("left@test.com")  # 로그인 세션 1개

    err(broken_admin.delete(f"{API}/admin/users/{u.id}"), 500, "INTERNAL_ERROR")
    db.expire_all()
    row = db.get(User, u.id)
    assert (row.name, row.email, row.status) == ("left", "left@test.com", "ACTIVE")  # 개인정보 덮어쓰기 취소
    assert db.scalar(select(Session).where(Session.user_id == u.id))  # 세션도 그대로
    client_for("left@test.com")  # 다시 로그인할 수 있음


# ---------- 활동 로그 ----------


def test_activity_log_filter_and_paging(db, admin):
    u = make_user(db, "m@test.com")
    c = client_for("m@test.com")
    c.post(f"{API}/auth/logout")
    client_for("m@test.com")

    page = admin.get(f"{API}/admin/users/{u.id}/activity", params={"operation": "LOGIN,LOGOUT"}).json()
    assert page["user"]["userId"] == u.id
    assert [a["operation"] for a in page["items"]] == ["LOGIN", "LOGOUT", "LOGIN"]  # 최신순
    assert set(page["items"][0]) == {"activityId", "operation", "targetLabel", "occurredAt"}

    first = admin.get(f"{API}/admin/users/{u.id}/activity", params={"limit": 2}).json()
    rest = admin.get(f"{API}/admin/users/{u.id}/activity", params={"limit": 2, "cursor": first["nextCursor"]}).json()
    assert len(first["items"]) == 2 and len(rest["items"]) == 1 and rest["nextCursor"] is None

    err(admin.get(f"{API}/admin/users/{u.id}/activity", params={"operation": "NOPE"}), 400, "INVALID_QUERY")


# ---------- 1단계: 등록·수정 예외 ----------


def test_concurrent_same_email_returns_409(db):
    """두 요청이 동시에 '이메일 없음'을 확인하고 저장하러 가도 한쪽은 409 (500이 아님)."""
    import threading

    from app.core.db import SessionLocal

    first, second = SessionLocal(), SessionLocal()
    result = {}
    try:
        create_user(first, name="a", email="race@test.com", role="MARKETING", password=PW)  # 저장했지만 아직 커밋 전

        def register_second():
            try:
                create_user(second, name="b", email="race@test.com", role="LEGAL", password=PW)
                second.commit()
                result["status"] = 201
            except ApiError as e:
                result["status"], result["code"] = e.status_code, e.code

        t = threading.Thread(target=register_second)
        t.start()
        t.join(timeout=0.5)
        assert t.is_alive()  # 두 번째는 '이메일 없음'을 확인한 뒤, 첫 번째 저장이 끝나길 DB에서 기다리는 중
        first.commit()
        t.join(timeout=5)
        assert result == {"status": 409, "code": "EMAIL_ALREADY_EXISTS"}
    finally:
        first.close()
        second.close()
    assert db.query(User).filter(User.email == "race@test.com").count() == 1


def test_register_length_rules(db, admin):
    url = f"{API}/admin/users"
    base = {"name": "새 사용자", "email": "new@test.com", "temporaryPassword": "temp1234", "role": "MARKETING"}
    # 길이 초과는 500이 아니라 422
    e = err(admin.post(url, json={**base, "name": "가" * 101}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "name", "code": "INVALID"}]
    e = err(admin.post(url, json={**base, "email": "a" * 250 + "@t.com"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "email", "code": "INVALID"}]


def test_update_rejects_empty_and_bad_values(db, admin):
    u = make_user(db, "edit@test.com")
    url = f"{API}/admin/users/{u.id}"
    for body in [{}, {"role": None}, {"role": None, "status": None}]:
        e = err(admin.patch(url, json=body), 422, "VALIDATION_ERROR")
        assert e["message"] == "변경할 항목을 입력해 주세요.", body
    e = err(admin.patch(url, json={"role": "SUPER"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "role", "code": "INVALID"}]
    e = err(admin.patch(url, json={"status": "PAUSED"}), 422, "VALIDATION_ERROR")
    assert e["fieldErrors"] == [{"field": "status", "code": "INVALID"}]
    assert not db.scalars(select(ActivityLog).where(ActivityLog.operation == "USER_UPDATED")).all()


def test_update_with_same_values_changes_nothing(db, admin):
    u = make_user(db, "same@test.com")
    client_for("same@test.com")  # 로그인 세션 1개
    res = admin.patch(f"{API}/admin/users/{u.id}", json={"role": "MARKETING", "status": "ACTIVE"})
    assert res.status_code == 200 and res.json()["role"] == "MARKETING"
    db.expire_all()
    assert not db.scalars(select(ActivityLog).where(ActivityLog.operation == "USER_UPDATED")).all()  # 로그 없음
    assert db.scalars(select(Session).where(Session.user_id == u.id)).all()  # 세션도 그대로
