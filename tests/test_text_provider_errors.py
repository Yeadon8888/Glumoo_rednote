"""Regression tests for actionable text-provider failures."""

import pytest


class _TextResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class _FailedTextService:
    def generate_outline(self, *args, **kwargs):
        return {
            "success": False,
            "error": "API 配额限制。",
            "error_code": "insufficient_user_quota",
        }

    def generate_content(self, *args, **kwargs):
        return {
            "success": False,
            "error": "API 配额限制。",
            "error_code": "insufficient_user_quota",
        }


def test_text_client_preserves_provider_quota_code(monkeypatch):
    from backend.utils.text_client import ProviderAPIError, TextChatClient

    class _Response:
        status_code = 403
        text = '{"error":{"message":"用户额度不足","code":"insufficient_user_quota"}}'

        def json(self):
            return {
                "error": {
                    "message": "用户额度不足",
                    "code": "insufficient_user_quota",
                }
            }

    monkeypatch.setattr(
        "backend.utils.text_client.requests.post",
        lambda *args, **kwargs: _Response(),
    )
    client = TextChatClient(api_key="test-key", base_url="https://example.com/v1")

    with pytest.raises(ProviderAPIError) as caught:
        client.generate_text(prompt="测试", model="gemini-3.5-flash")

    assert caught.value.status_code == 403
    assert caught.value.code == "insufficient_user_quota"


def test_text_client_retries_temporary_503(monkeypatch):
    from backend.utils.text_client import TextChatClient

    responses = iter([
        _TextResponse(
            503,
            {"error": {"message": "upstream temporarily unavailable"}},
        ),
        _TextResponse(
            200,
            {"choices": [{"message": {"content": "大纲生成成功"}}]},
        ),
    ])
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return next(responses)

    monkeypatch.setattr("backend.utils.text_client.requests.post", fake_post)
    monkeypatch.setattr("backend.utils.text_client.time.sleep", lambda _: None)
    client = TextChatClient(api_key="test-key", base_url="https://example.com/v1")

    result = client.generate_text(prompt="测试", model="gemini-3.5-flash")

    assert result == "大纲生成成功"
    assert len(calls) == 2


def test_outline_quota_failure_returns_payment_required(client, monkeypatch):
    monkeypatch.setattr(
        "backend.routes.outline_routes.get_outline_service",
        lambda: _FailedTextService(),
    )

    response = client.post("/api/outline", json={"topic": "测试主题"})

    assert response.status_code == 402
    assert response.get_json() == {
        "success": False,
        "error": "TokensFactory 账户余额不足，请充值后重试。",
        "error_code": "insufficient_user_quota",
    }


def test_content_quota_failure_returns_payment_required(client, monkeypatch):
    monkeypatch.setattr(
        "backend.routes.content_routes.get_content_service",
        lambda: _FailedTextService(),
    )

    response = client.post(
        "/api/content",
        json={"topic": "测试主题", "outline": "测试大纲"},
    )

    assert response.status_code == 402
    assert response.get_json() == {
        "success": False,
        "error": "TokensFactory 账户余额不足，请充值后重试。",
        "error_code": "insufficient_user_quota",
    }
