"""
apps/api/telegram.py — Telegram update parsing, auth, and outbound (Milestone D, D2–D3).

Parsing and auth are pure functions over a Telegram webhook payload — no
network, no HTTP client, no model call. The outbound `send_message` is the
single HTTP call this module makes; it takes an injected `http` so tests
never touch the network.

The shape of a Telegram update this module cares about (only the subset we
consume):

    {
      "update_id": 123456789,
      "message": {
        "message_id": 42,
        "from": {"id": 8320302098, ...},
        "chat": {"id": 8320302098, "type": "private", ...},
        "date": 1728268800,
        "text": "hello"
      }
    }

Telegram sends many other update kinds (edited_message, channel_post,
callback_query, my_chat_member, etc.). `parse_update` returns None for any
of them — the caller treats None as "nothing to do" and responds 200 OK
silently, which is the destination §11 requirement: reject everything else
without leaking which users exist or which update kinds are handled.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests

from apps.api.settings import ApiSettings
from core.config import redact_credentials


TELEGRAM_API_BASE = "https://api.telegram.org"

# Telegram bot tokens in a URL path: `bot<digits>:<base64-ish>`. Covers
# https://api.telegram.org/bot<token>/... — a shape core.config's redactor
# (built for user:pass@ URLs and password=... key-values) does not match.
_TELEGRAM_TOKEN_RE = re.compile(r"bot\d+:[A-Za-z0-9_-]+")


def _redact(text: str) -> str:
    """Apply core redaction, then mask any Telegram bot token in a URL path.

    Order matters: redact_credentials first (so its three patterns see the
    original string), then the Telegram-specific pass (which catches the
    bot<token> URL-path shape the core redactor does not know about). Two
    passes are safe — neither can produce a false positive that erases
    real text.
    """
    return _TELEGRAM_TOKEN_RE.sub("bot***", redact_credentials(text))


@dataclass(frozen=True)
class IncomingMessage:
    """The four fields this layer needs from a Telegram message update.

    `update_id` is included because Telegram retries on timeout and reuses
    the same update_id — D4's handler will use it for idempotency if retries
    become a real problem, and it is the natural correlation key for logs.
    """

    update_id: int
    user_id: int
    chat_id: int
    text: str


def parse_update(payload: Any) -> IncomingMessage | None:
    """Extract an IncomingMessage from a Telegram update dict.

    Returns None for anything that is not a plain text message from a user:
    non-dict payloads, missing keys, non-message updates, edits, channel
    posts, empty or non-string text, or fields of the wrong type.

    Never raises on malformed input — Telegram will send things this code
    does not recognize, and the correct response is to ignore them, not to
    crash the webhook handler. The webhook responds 200 OK either way.
    """
    if not isinstance(payload, dict):
        return None

    update_id = payload.get("update_id")
    if not isinstance(update_id, int):
        return None

    message = payload.get("message")
    if not isinstance(message, dict):
        return None

    sender = message.get("from")
    if not isinstance(sender, dict):
        return None
    user_id = sender.get("id")
    if not isinstance(user_id, int):
        return None

    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return None

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    return IncomingMessage(
        update_id=update_id,
        user_id=user_id,
        chat_id=chat_id,
        text=text,
    )


def is_authorized(user_id: int, settings: ApiSettings) -> bool:
    """True iff user_id is in the configured allowlist.

    An empty allowlist denies everyone — the default is closed. This is the
    destination §11 minimum-bar auth (D015): user-id allowlist plus the
    webhook secret header checked at the HTTP layer in D4. Both must pass.
    """
    return user_id in settings.telegram_allowed_user_ids


# ---------------------------------------------------------------------------
# Outbound: send a message back to a chat (D3)
# ---------------------------------------------------------------------------


class TelegramSendError(Exception):
    """Raised when the sendMessage call fails.

    Wraps every failure mode — empty token, transport error, non-2xx
    response — so D4's webhook handler has one exception type to catch and
    can log the failure without letting it 500 the webhook. All error text
    passes through `_redact` before being raised, so neither a `user:pass@`
    URL nor a `bot<token>` URL path can leak into a traceback (D013).
    """


def send_message(
    chat_id: int,
    text: str,
    settings: ApiSettings,
    *,
    http=requests,
) -> None:
    """Send `text` to `chat_id` via Telegram's sendMessage endpoint.

    The URL is https://api.telegram.org/bot<token>/sendMessage with a JSON
    body {"chat_id": <int>, "text": <str>}. `http` is injectable — tests
    pass a fake that records the call and returns a fake response, so no
    test touches the network. In production the default is `requests`.

    Returns None on success. Raises TelegramSendError on any failure: an
    empty token, a transport error (requests.RequestException), or a non-2xx
    response. No retry here — the caller decides policy, matching how
    core.models.retry wraps provider.generate rather than baking retries
    into the provider.
    """
    token = settings.telegram_bot_token
    if not token:
        raise TelegramSendError(
            "TELEGRAM_BOT_TOKEN is not configured; cannot send message."
        )

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    body = {"chat_id": chat_id, "text": text}

    try:
        response = http.post(url, json=body, timeout=10)
    except requests.RequestException as exc:
        raise TelegramSendError(
            f"Telegram sendMessage transport error: {_redact(str(exc))}"
        ) from exc

    status = getattr(response, "status_code", None)
    if status is None or status < 200 or status >= 300:
        snippet = ""
        try:
            snippet = response.text[:200]
        except Exception:
            snippet = "<unreadable response body>"
        raise TelegramSendError(
            f"Telegram sendMessage failed: HTTP {status}: {_redact(snippet)}"
        )
