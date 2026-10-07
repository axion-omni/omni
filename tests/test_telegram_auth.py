"""
Tests for apps/api/telegram.py — D2 update parsing and allowlist auth.

Fixture payloads only. No network, no env, no real credentials. Matches the
injection discipline of tests/test_cli.py: a real `core.config.Settings` with
"fake" creds, wrapped in an `ApiSettings` with fake Telegram fields.
"""

from __future__ import annotations

from apps.api.settings import ApiSettings
from apps.api.telegram import IncomingMessage, is_authorized, parse_update
from core.config import Settings


ALLOWED_USER_ID = 8320302098
OTHER_USER_ID = 9999999999


def _fake_engine_settings() -> Settings:
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
        model_fallback="",
    )


def _api_settings(allowed: tuple[int, ...] = (ALLOWED_USER_ID,)) -> ApiSettings:
    return ApiSettings(
        engine=_fake_engine_settings(),
        telegram_bot_token="fake-token",
        telegram_allowed_user_ids=allowed,
        telegram_webhook_secret="fake-secret",
        public_base_url="https://example.invalid",
    )


def _text_update(
    *,
    update_id: int = 1001,
    user_id: int = ALLOWED_USER_ID,
    chat_id: int = ALLOWED_USER_ID,
    text: str = "hello",
) -> dict:
    """A minimal, realistic Telegram text-message update."""
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


# ---------------------------------------------------------------------------
# parse_update — happy path
# ---------------------------------------------------------------------------


def test_parse_update_extracts_all_four_fields():
    msg = parse_update(_text_update())

    assert msg == IncomingMessage(
        update_id=1001,
        user_id=ALLOWED_USER_ID,
        chat_id=ALLOWED_USER_ID,
        text="hello",
    )


def test_parse_update_handles_group_chat_where_user_and_chat_differ():
    msg = parse_update(
        _text_update(user_id=ALLOWED_USER_ID, chat_id=-1001234567890)
    )

    assert msg is not None
    assert msg.user_id == ALLOWED_USER_ID
    assert msg.chat_id == -1001234567890


# ---------------------------------------------------------------------------
# parse_update — rejections (all must return None, never raise)
# ---------------------------------------------------------------------------


def test_parse_update_rejects_non_dict():
    assert parse_update("not a dict") is None
    assert parse_update(None) is None
    assert parse_update(42) is None
    assert parse_update([1, 2, 3]) is None


def test_parse_update_rejects_missing_update_id():
    payload = _text_update()
    del payload["update_id"]
    assert parse_update(payload) is None


def test_parse_update_rejects_non_int_update_id():
    payload = _text_update()
    payload["update_id"] = "1001"  # string, not int
    assert parse_update(payload) is None


def test_parse_update_rejects_non_message_update():
    # edited_message, channel_post, callback_query, etc. — all ignored.
    payload = {
        "update_id": 1001,
        "edited_message": {
            "message_id": 42,
            "from": {"id": ALLOWED_USER_ID},
            "chat": {"id": ALLOWED_USER_ID},
            "text": "edited",
        },
    }
    assert parse_update(payload) is None


def test_parse_update_rejects_missing_from():
    payload = _text_update()
    del payload["message"]["from"]
    assert parse_update(payload) is None


def test_parse_update_rejects_missing_chat():
    payload = _text_update()
    del payload["message"]["chat"]
    assert parse_update(payload) is None


def test_parse_update_rejects_empty_text():
    assert parse_update(_text_update(text="")) is None
    assert parse_update(_text_update(text="   ")) is None


def test_parse_update_rejects_non_string_text():
    payload = _text_update()
    payload["message"]["text"] = 12345
    assert parse_update(payload) is None


def test_parse_update_rejects_wrong_type_user_id():
    payload = _text_update()
    payload["message"]["from"]["id"] = "8320302098"  # string, not int
    assert parse_update(payload) is None


# ---------------------------------------------------------------------------
# is_authorized
# ---------------------------------------------------------------------------


def test_is_authorized_allows_listed_user():
    assert is_authorized(ALLOWED_USER_ID, _api_settings()) is True


def test_is_authorized_rejects_unlisted_user():
    assert is_authorized(OTHER_USER_ID, _api_settings()) is False


def test_is_authorized_empty_allowlist_denies_everyone():
    assert is_authorized(ALLOWED_USER_ID, _api_settings(allowed=())) is False


def test_is_authorized_allows_any_listed_user():
    settings = _api_settings(allowed=(111, 222, ALLOWED_USER_ID, 444))
    assert is_authorized(ALLOWED_USER_ID, settings) is True
    assert is_authorized(111, settings) is True
    assert is_authorized(333, settings) is False


# ---------------------------------------------------------------------------
# ApiSettings repr — the D013/D014 discipline applied to the interface layer
# ---------------------------------------------------------------------------


def test_api_settings_repr_masks_secrets():
    settings = _api_settings()
    text = repr(settings)

    assert "fake-token" not in text
    assert "fake-secret" not in text
    assert "***" in text


def test_api_settings_repr_delegates_to_engine_repr():
    # The engine settings' own repr already masks the DB URL password; the
    # ApiSettings repr must not bypass that by printing fields directly.
    settings = _api_settings()
    text = repr(settings)

    # The wrapped engine repr appears inside, masked.
    assert "engine=Settings(" in text
