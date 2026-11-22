import base64


def _basic_header(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_site_auth_is_disabled_without_environment(client):
    response = client.get("/")

    assert response.status_code == 200


def test_site_auth_protects_pages_and_api_but_not_health(monkeypatch):
    monkeypatch.setenv("APP_AUTH_USERNAME", "site-user")
    monkeypatch.setenv("APP_AUTH_PASSWORD", "site-password")

    from backend.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    page_response = client.get("/")
    assert page_response.status_code == 401
    assert page_response.headers["WWW-Authenticate"].startswith("Basic ")

    api_response = client.get("/api/config")
    assert api_response.status_code == 401
    assert api_response.get_json()["error"] == "需要访问密码"

    wrong_response = client.get(
        "/", headers=_basic_header("site-user", "wrong-password")
    )
    assert wrong_response.status_code == 401

    authenticated_response = client.get(
        "/", headers=_basic_header("site-user", "site-password")
    )
    assert authenticated_response.status_code == 200

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.get_json()["status"] == "healthy"


def test_remembered_browser_can_reopen_and_password_rotation_revokes_login(client, monkeypatch):
    from backend.auth import COOKIE_NAME
    monkeypatch.setenv("APP_AUTH_USERNAME", "site-user")
    monkeypatch.setenv("APP_AUTH_PASSWORD", "site-password")
    monkeypatch.setenv("APP_AUTH_COOKIE_KEY", "independent-test-key")
    headers = dict(_basic_header("site-user", "site-password"), Accept="text/html")
    response = client.get("/", headers=headers, base_url="https://localhost")
    cookie = response.headers["Set-Cookie"]
    for parameter in ("Max-Age=2592000", "HttpOnly", "Secure", "SameSite=Lax"):
        assert parameter in cookie
    assert "site-password" not in cookie
    assert client.get("/history", base_url="https://localhost").status_code == 200
    assert client.post("/api/config", headers={"Origin": "https://other.example"}).status_code == 403
    monkeypatch.setenv("APP_AUTH_PASSWORD", "changed")
    assert client.get("/api/config").status_code == 401
    client.set_cookie(COOKIE_NAME, "invalid")
    assert client.get("/").status_code == 401


def test_expired_browser_login_requires_credentials(client, monkeypatch):
    import time
    from backend.auth import REMEMBER_SECONDS
    monkeypatch.setenv("APP_AUTH_USERNAME", "site-user")
    monkeypatch.setenv("APP_AUTH_PASSWORD", "site-password")
    monkeypatch.setenv("APP_AUTH_COOKIE_KEY", "independent-test-key")
    client.get("/", headers=dict(_basic_header("site-user", "site-password"), Accept="text/html"))
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now + REMEMBER_SECONDS + 1)
    assert client.get("/api/config").status_code == 401
