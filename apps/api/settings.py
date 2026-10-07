"""
apps/api/settings.py — interface-layer configuration wrapper.

Milestone D introduces a small set of configuration that belongs to the
*interface* (Telegram bot token, allowed user ids, webhook secret, public
base URL) but has no business living inside the engine. Per D003 the engine
stays headless and knows nothing about Telegram; per D014 the engine's
`core.config.Settings` is owned by the engine chat and is not edited here.

This module is the seam. It wraps a `core.config.Settings` (the engine
settings) inside an `ApiSettings` (the interface settings) so the API can
carry both without either owning the other.

Credential safety mirrors core/config.py's discipline: `ApiSettings.__repr__`
masks `telegram_bot_token` and `telegram_webhook_secret`, so a pytest
traceback or any log line that prints an ApiSettings cannot leak either.
This is the D013/D014 rule applied to the interface layer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from core.config import Settings, load_settings


def _parse_allowed_user_ids(raw: str) -> tuple[int, ...]:
    """Parse TELEGRAM_ALLOWED_USER_IDS as a comma-separated list of ints.

    Empty / whitespace-only -> () (deny everyone; the default is closed).
    Rigid by design: a non-integer entry raises ValueError at Settings
    construction, not at the first webhook call, so a misconfigured allowlist
    fails loudly at startup rather than silently denying (or, worse,
    accepting) the wrong user.
    """
    raw = (raw or "").strip()
    if not raw:
        return ()
    try:
        return tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    except ValueError as exc:
        raise ValueError(
            f"TELEGRAM_ALLOWED_USER_IDS must be a comma-separated list of "
            f"integers, got {raw!r}: {exc}"
        ) from exc


@dataclass(frozen=True)
class ApiSettings:
    """Interface-layer settings. Wraps the engine settings; does not replace
    them. Fields added here must never require editing `core/`."""

    engine: Settings

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: tuple[int, ...] = ()
    telegram_webhook_secret: str = ""
    public_base_url: str = ""

    def __repr__(self) -> str:
        """Credential-safe repr. The bot token and webhook secret are the
        two secrets at this layer; both are masked. The engine settings are
        already masked by their own repr, so we delegate to it."""
        return (
            "ApiSettings("
            f"engine={self.engine!r}, "
            f"telegram_bot_token={'***' if self.telegram_bot_token else ''!r}, "
            f"telegram_allowed_user_ids={self.telegram_allowed_user_ids!r}, "
            f"telegram_webhook_secret={'***' if self.telegram_webhook_secret else ''!r}, "
            f"public_base_url={self.public_base_url!r}"
            ")"
        )


def load_api_settings() -> ApiSettings:
    """Construct ApiSettings from the environment.

    Delegates engine settings to `core.config.load_settings()` (the single
    env-reading seam for the engine) and reads the four Telegram-specific
    env vars here. Nothing outside this module should call `os.environ`
    directly — same discipline as `core/config.py`.
    """
    return ApiSettings(
        engine=load_settings(),
        telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        telegram_allowed_user_ids=_parse_allowed_user_ids(
            os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
        ),
        telegram_webhook_secret=os.environ.get("TELEGRAM_WEBHOOK_SECRET", ""),
        public_base_url=os.environ.get("PUBLIC_BASE_URL", ""),
    )
