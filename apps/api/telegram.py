"""
apps/api/telegram.py — Telegram update parsing and auth (Milestone D, D2).

Pure functions over a Telegram webhook payload. No network, no HTTP client,
no model call. D3 adds the outbound `send_message`; D4 wires the webhook
handler in `apps/api/app.py` to call into here.

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

from dataclasses import dataclass
from typing import Any

from apps.api.settings import ApiSettings


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
