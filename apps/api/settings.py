"""
apps/api/settings.py — interface-layer configuration wrapper.

Milestone D introduces a small set of configuration that belongs to the
*interface* (Telegram bot token, allowed user ids, webhook secret, public
base URL) but has no business living inside the engine. Per D003 the engine
stays headless and knows nothing about Telegram; per D013/D014 the engine's
`core.config.Settings` is owned by the engine chat and is not edited here.

This module is the seam. It wraps a `core.config.Settings` (the engine
settings) inside an `ApiSettings` (the interface settings) so the API can
carry both without either owning the other.

In D1 the wrapper carries only the engine settings. D2 adds the Telegram
fields and a masking `__repr__` — but `create_app`'s signature stays
`create_app(settings: ApiSettings)`, so no caller churn between D1 and D5.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.config import Settings, load_settings


@dataclass(frozen=True)
class ApiSettings:
    """Interface-layer settings. Wraps the engine settings; does not replace
    them. Fields added here must never require editing `core/`."""

    engine: Settings


def load_api_settings() -> ApiSettings:
    """Construct ApiSettings from the environment.

    Delegates engine settings to `core.config.load_settings()` (the single
    env-reading seam for the engine). D2 will extend this to read the
    Telegram-specific env vars. Nothing outside this module should call
    `os.environ` directly — same discipline as `core/config.py`.
    """
    return ApiSettings(engine=load_settings())
