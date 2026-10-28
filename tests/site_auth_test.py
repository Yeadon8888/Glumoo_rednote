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
