"""Optional site-wide HTTP Basic authentication."""

import os
import secrets

from flask import Response, jsonify, request


AUTH_USERNAME_ENV = "APP_AUTH_USERNAME"
AUTH_PASSWORD_ENV = "APP_AUTH_PASSWORD"
PUBLIC_PATHS = frozenset({"/api/health"})


def register_site_auth(app) -> None:
    """Protect the site when both authentication environment variables are set."""

    @app.before_request
    def require_site_auth():
        username = os.getenv(AUTH_USERNAME_ENV, "")
        password = os.getenv(AUTH_PASSWORD_ENV, "")

        if not username or not password:
            return None
        if request.method == "OPTIONS" or request.path in PUBLIC_PATHS:
            return None

        credentials = request.authorization
        if credentials and credentials.type.lower() == "basic":
            username_matches = secrets.compare_digest(
                credentials.username or "", username
            )
            password_matches = secrets.compare_digest(
                credentials.password or "", password
            )
            if username_matches and password_matches:
                return None

        headers = {
            "WWW-Authenticate": 'Basic realm="Glumoo", charset="UTF-8"',
            "Cache-Control": "no-store",
        }
        if request.path.startswith("/api/"):
            response = jsonify({
                "success": False,
                "error": "需要访问密码",
            })
            response.status_code = 401
            response.headers.extend(headers)
            return response

        return Response("需要访问密码", status=401, headers=headers)

