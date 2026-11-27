"""CORS: 프론트 주소(localhost:5173)에서 오는 요청과 쿠키를 허용하는지 확인.
Origin 검사: 다른 사이트에서 보낸 POST·PATCH·DELETE는 403으로 거절하는지 확인."""

FRONT = "http://localhost:5173"


def test_preflight_allows_front_with_cookies(client):
    res = client.options(
        "/api/v1/auth/login",
        headers={"Origin": FRONT, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == FRONT
    assert res.headers["access-control-allow-credentials"] == "true"


def test_response_exposes_headers_to_front(client):
    res = client.get("/api/v1/me", headers={"Origin": FRONT})  # 401이어도 CORS 헤더는 붙어야 프론트가 오류를 읽음
    assert res.status_code == 401
    assert res.headers["access-control-allow-origin"] == FRONT
    exposed = res.headers["access-control-expose-headers"].lower()
    assert "content-disposition" in exposed and "location" in exposed


def test_other_origin_is_not_allowed(client):
    res = client.get("/api/v1/me", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in res.headers


# ---------- Origin 검사 (CSRF 보완) ----------

EVIL = "http://evil.example"
LOGIN = "/api/v1/auth/login"
BODY = {"email": "nobody@test.com", "password": "password123"}


def test_other_site_post_is_403(client):
    res = client.post(LOGIN, json=BODY, headers={"Origin": EVIL})
    assert res.status_code == 403
    err = res.json()["error"]
    assert err["code"] == "FORBIDDEN" and err["requestId"].startswith("req_")
    assert res.headers["X-Request-ID"] == err["requestId"]


def test_other_site_blocked_for_all_change_methods(admin):
    for method in ("post", "patch", "delete"):
        res = getattr(admin, method)("/api/v1/admin/users/usr_999", headers={"Origin": "null"})
        assert res.status_code == 403, method


def test_front_origin_passes(client):
    res = client.post(LOGIN, json=BODY, headers={"Origin": FRONT})
    assert res.json()["error"]["code"] == "USER_NOT_FOUND"  # Origin 검사는 통과, 로그인 단계에서 거절


def test_swagger_same_origin_passes(client):
    res = client.post(LOGIN, json=BODY, headers={"Origin": "http://testserver"})  # 백엔드 자기 주소
    assert res.json()["error"]["code"] == "USER_NOT_FOUND"


def test_no_origin_passes(client):
    assert client.post(LOGIN, json=BODY).json()["error"]["code"] == "USER_NOT_FOUND"


def test_get_and_internal_are_not_checked(client):
    assert client.get("/api/v1/me", headers={"Origin": EVIL}).status_code == 401  # 조회는 데이터를 바꾸지 않음
    res = client.post("/internal/v1/review-runs/run_001/completion", json={}, headers={"Origin": EVIL})
    assert res.status_code == 401  # Agent 내부 API는 토큰으로 판단
