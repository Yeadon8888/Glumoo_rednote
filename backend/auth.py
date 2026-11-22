"""Site-wide Basic authentication with a persistent browser login."""
import hashlib
import hmac
import json
import os
import secrets

from flask import Response, g, jsonify, request
from itsdangerous import BadData, URLSafeTimedSerializer

AUTH_USERNAME_ENV = "APP_AUTH_USERNAME"
AUTH_PASSWORD_ENV = "APP_AUTH_PASSWORD"
COOKIE_NAME = "__Host-glumoo_login"
REMEMBER_SECONDS = 30 * 24 * 60 * 60
PUBLIC_PATHS = frozenset({"/api/health"})


def _login_signer(username, password):
    key = os.getenv("APP_AUTH_COOKIE_KEY")
    if not key:
        return None
    # Changing the site credentials invalidates every existing browser login.
    credentials = json.dumps([username, password]).encode()
    signing_key = hmac.digest(key.encode(), credentials, hashlib.sha256)
    return URLSafeTimedSerializer(signing_key, salt="glumoo.browser-login.v1")


def register_site_auth(app) -> None:
    @app.before_request
    def require_site_auth():
        username = os.getenv(AUTH_USERNAME_ENV, "")
        password = os.getenv(AUTH_PASSWORD_ENV, "")
        if not username or not password or request.method == "OPTIONS" or request.path in PUBLIC_PATHS:
            return None

        signer = _login_signer(username, password)
        credentials = request.authorization
        token = request.cookies.get(COOKIE_NAME)
        if signer and token:
            try:
                if signer.loads(token, max_age=REMEMBER_SECONDS) == "signed-in":
                    if request.method not in {"GET", "HEAD"}:
                        origin = request.headers.get("Origin")
                        if request.headers.get("Sec-Fetch-Site") == "cross-site" or (
                            origin and origin != "https://" + request.host
                        ):
                            return jsonify(success=False, error="请从本站重新操作"), 403
                    return None
            except BadData:
                pass

        if credentials and credentials.type.lower() == "basic":
            username_ok = secrets.compare_digest((credentials.username or "").encode(), username.encode())
            password_ok = secrets.compare_digest((credentials.password or "").encode(), password.encode())
            if username_ok and password_ok:
                if signer and request.method == "GET" and not request.path.startswith("/api/") and (
                    request.headers.get("Sec-Fetch-Dest") == "document" or
                    "text/html" in request.headers.get("Accept", "")
                ):
                    g.browser_login = signer.dumps("signed-in")
                return None

        headers = {"WWW-Authenticate": 'Basic realm="Glumoo", charset="UTF-8"', "Cache-Control": "no-store"}
        if request.path.startswith("/api/"):
            response = jsonify(success=False, error="需要访问密码")
            response.status_code = 401
            response.headers.extend(headers)
            return response
        return Response("需要访问密码", status=401, headers=headers)

    @app.after_request
    def remember_browser(response):
        token = g.get("browser_login")
        if token and response.status_code < 400:
            response.set_cookie(COOKIE_NAME, token, max_age=REMEMBER_SECONDS, secure=True,
                                httponly=True, samesite="Lax", path="/")
            response.cache_control.no_store = True
        return response
