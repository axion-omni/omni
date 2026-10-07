"""
Tests for the /telegram/webhook handler — D4.

The registry builder and the Telegram http client are both injected, so
nothing here touches the network or a real model. Fixture updates only.
Same injection discipline as tests/test_cli.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from apps.api.settings import ApiSettings
from core.config import Settings
from core.models.base import ModelResponse
from core.models.exceptions import ModelUnavailableError


ALLOWED_USER_ID = 8320302098
OTHER_USER_ID = 9999999999
WEBHOOK_SECRET = "test-secret"


def _fake_engine_settings() -> Settings:
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
        model_fallback="",
    )


def _api_settings() -> ApiSettings:
    return ApiSettings(
        engine=_fake_engine_settings(),
        telegram_bot_token="fake-token",
        telegram_allowed_user_ids=(ALLOWED_USER_ID,),
        telegram_webhook_secret=WEBHOOK_SECRET,
        public_base_url="https://example.invalid",
    )


def _text_update(
    *,
    update_id: int = 1001,
    user_id: int = ALLOWED_USER_ID,
    chat_id: int = ALLOWED_USER_ID,
    text: str = "hello",
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 42,
            "from": {"id": user_id, "is_bot": False, "first_name": "Op"},
            "chat": {"id": chat_id, "type": "private"},
            "date": 1728268800,
            "text": text,
        },
    }


class _FakeProvider:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.generate_called_with: dict | None = None

    def generate(self, prompt, **kwargs):
        self.generate_called_with = {"prompt": prompt, **kwargs}
        if self._error is not None:
            raise self._error
        return self._response


class _FakeRegistry:
    def __init__(self, provider):
        self._provider = provider
        self.resolved: list[str] = []

    def resolve(self, logical_name):
        self.resolved.append(logical_name)
        return self._provider, "claude-sonnet-5"


def _model_response(text="hello from the model"):
    return ModelResponse(
        text=text,
        model="claude-sonnet-5",
        provider="anthropic",
        input_tokens=5,
        output_tokens=2,
    )


class _FakeHttpResponse:
    def __init__(self, status_code=200, text='{"ok":true}'):
        self.status_code = status_code
        self.text = text


class _FakeTelegramHttp:
    """Records send_message POSTs; returns 200 by default."""

    def __init__(self, response=None):
        self._response = response or _FakeHttpResponse()
        self.calls: list[dict] = []

    def post(self, url, *, json=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return self._response


def _client(provider=None, http=None):
    provider = provider or _FakeProvider(response=_model_response())
    registry = _FakeRegistry(provider)
    http = http or _FakeTelegramHttp()
    app = create_app(
        _api_settings(),
        registry_builder=lambda settings: registry,
        http=http,
    )
    return TestClient(app), registry, provider, http


def _post_webhook(client, payload, secret=WEBHOOK_SECRET):
    headers = {}
    if secret is not None:
        headers["X-Telegram-Bot-Api-Secret-Token"] = secret
    return client.post("/telegram/webhook", json=payload, headers=headers)


# ---------------------------------------------------------------------------
# Happy path — the only branch that sends a reply
# ---------------------------------------------------------------------------


def test_authorized_message_produces_reply():
    client, registry, provider, http = _client()

    response = _post_webhook(client, _text_update(text="hello"))

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(http.calls) == 1
    assert http.calls[0]["json"]["chat_id"] == ALLOWED_USER_ID
    assert http.calls[0]["json"]["text"] == "hello from the model"
    # the engine was actually exercised
    assert registry.resolved == ["reasoning-strong"]
    assert provider.generate_called_with["prompt"] == "hello"


# ---------------------------------------------------------------------------
# Silent rejections — all return 200 {"ok": true}, no send_message
# ---------------------------------------------------------------------------


def test_missing_secret_header_is_rejected_silently():
    client, registry, provider, http = _client()

    response = _post_webhook(client, _text_update(), secret=None)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert http.calls == []
    assert registry.resolved == []


def test_wrong_secret_header_is_rejected_silently():
    client, registry, provider, http = _client()

    response = _post_webhook(client, _text_update(), secret="wrong-secret")

    assert response.status_code == 200
    assert http.calls == []
    assert registry.resolved == []


def test_unauthorized_user_is_rejected_silently():
    client, registry, provider, http = _client()

    response = _post_webhook(client, _text_update(user_id=OTHER_USER_ID))

    assert response.status_code == 200
    assert http.calls == []
    # allowlist rejected before the engine was reached
    assert registry.resolved == []


def test_unparseable_update_is_ignored_silently():
    client, registry, provider, http = _client()

    # edited_message, not message — parse_update returns None
    payload = {
        "update_id": 1001,
        "edited_message": {
            "message_id": 42,
            "from": {"id": ALLOWED_USER_ID},
            "chat": {"id": ALLOWED_USER_ID},
            "text": "edited",
        },
    }
    response = _post_webhook(client, payload)

    assert response.status_code == 200
    assert http.calls == []
    assert registry.resolved == []


# ---------------------------------------------------------------------------
# Failure branches that still return 200 (no retry from Telegram)
# ---------------------------------------------------------------------------


def test_model_error_returns_200_without_send():
    provider = _FakeProvider(error=ModelUnavailableError("provider down"))
    client, registry, provider, http = _client(provider=provider)

    response = _post_webhook(client, _text_update())

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert http.calls == []


def test_send_failure_returns_200():
    http = _FakeTelegramHttp(response=_FakeHttpResponse(status_code=401))
    client, registry, provider, http = _client(http=http)

    response = _post_webhook(client, _text_update())

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # the send was attempted and failed; no second attempt
    assert len(http.calls) == 1


# ---------------------------------------------------------------------------
# Response body uniformity — no branch leaks which path was taken
# ---------------------------------------------------------------------------


def test_all_outcomes_return_same_body():
    client, *_ = _client()

    # unauthorized user
    r1 = _post_webhook(client, _text_update(user_id=OTHER_USER_ID))
    # bad secret
    r2 = _post_webhook(client, _text_update(), secret="wrong")
    # parseable but non-message
    r3 = _post_webhook(client, {"update_id": 1, "edited_message": {}})

    assert r1.json() == r2.json() == r3.json() == {"ok": True}
