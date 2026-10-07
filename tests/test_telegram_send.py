"""
Tests for apps/api/telegram.py::send_message — D3 outbound client.

An injected fake `http` records the call and returns a fake response, so
this file never touches the network. Same injection discipline as
tests/test_cli.py and tests/test_retry.py.
"""

from __future__ import annotations

import pytest
import requests

from apps.api.settings import ApiSettings
from apps.api.telegram import TelegramSendError, send_message
from core.config import Settings


CHAT_ID = 8320302098


def _fake_engine_settings() -> Settings:
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
        model_fallback="",
    )


def _api_settings(token: str = "fake-token") -> ApiSettings:
    return ApiSettings(
        engine=_fake_engine_settings(),
        telegram_bot_token=token,
        telegram_allowed_user_ids=(CHAT_ID,),
        telegram_webhook_secret="fake-secret",
        public_base_url="https://example.invalid",
    )


class _FakeResponse:
    def __init__(self, status_code: int = 200, text: str = '{"ok":true}'):
        self.status_code = status_code
        self.text = text


class _FakeHttp:
    """Records the single call send_message makes."""

    def __init__(self, response=None, raise_exc=None):
        self._response = response or _FakeResponse()
        self._raise = raise_exc
        self.calls: list[dict] = []

    def post(self, url, *, json=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        if self._raise is not None:
            raise self._raise
        return self._response


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_send_message_builds_correct_url_and_body():
    http = _FakeHttp()

    send_message(CHAT_ID, "hello back", _api_settings(), http=http)

    assert len(http.calls) == 1
    call = http.calls[0]
    assert call["url"] == "https://api.telegram.org/botfake-token/sendMessage"
    assert call["json"] == {"chat_id": CHAT_ID, "text": "hello back"}


def test_send_message_returns_none_on_success():
    http = _FakeHttp(response=_FakeResponse(status_code=200))
    assert send_message(CHAT_ID, "hi", _api_settings(), http=http) is None


def test_send_message_accepts_2xx_other_than_200():
    # Telegram returns 200 on success; be tolerant of any 2xx.
    http = _FakeHttp(response=_FakeResponse(status_code=201))
    send_message(CHAT_ID, "hi", _api_settings(), http=http)


# ---------------------------------------------------------------------------
# Failure paths — all raise TelegramSendError, never leak requests' exceptions
# ---------------------------------------------------------------------------


def test_send_message_raises_on_empty_token_without_calling_http():
    http = _FakeHttp()

    with pytest.raises(TelegramSendError, match="TELEGRAM_BOT_TOKEN"):
        send_message(CHAT_ID, "hi", _api_settings(token=""), http=http)

    assert http.calls == []  # no HTTP attempted


def test_send_message_raises_on_non_2xx():
    http = _FakeHttp(response=_FakeResponse(status_code=401, text='{"ok":false}'))

    with pytest.raises(TelegramSendError, match="HTTP 401"):
        send_message(CHAT_ID, "hi", _api_settings(), http=http)


def test_send_message_wraps_transport_errors():
    http = _FakeHttp(raise_exc=requests.ConnectionError("connection refused"))

    with pytest.raises(TelegramSendError, match="transport error"):
        send_message(CHAT_ID, "hi", _api_settings(), http=http)


def test_send_message_redacts_token_from_error_message():
    # If a transport error's string contains the token (e.g. some proxies
    # embed the URL), the raised message must not carry it. The redaction
    # regex in core.config matches `://user:pass@` and `password=...` forms;
    # a bot token in a URL path is not matched by that regex, so this test
    # asserts the discipline holds for the shapes the regex covers.
    http = _FakeHttp(
        raise_exc=requests.ConnectionError(
            "failed to connect to https://user:sekret@api.telegram.org"
        )
    )

    with pytest.raises(TelegramSendError) as exc_info:
        send_message(CHAT_ID, "hi", _api_settings(), http=http)

    assert "sekret" not in str(exc_info.value)
    assert "***" in str(exc_info.value)


def test_send_message_masks_telegram_token_in_url_path():
    # A transport error that echoes the full URL would contain `bot<token>`
    # in the path — a shape core.config.redact_credentials does not match.
    # _redact in apps/api/telegram.py must mask it.
    http = _FakeHttp(
        raise_exc=requests.ConnectionError(
            "failed POST to https://api.telegram.org/bot8320302098:ABC-DEF_xyz/sendMessage"
        )
    )

    with pytest.raises(TelegramSendError) as exc_info:
        send_message(CHAT_ID, "hi", _api_settings(), http=http)

    text = str(exc_info.value)
    assert "8320302098:ABC-DEF_xyz" not in text
    assert "bot***" in text
