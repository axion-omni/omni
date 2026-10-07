"""
apps/api/app.py — FastAPI cloud API (Milestone D).

D1 built the skeleton and /health. D4 wires the Telegram webhook: a push
from Telegram is authenticated (secret header + user allowlist), parsed,
routed through the engine (routing -> registry -> generate_with_retry), and
the reply is sent back through send_message.

Per D003 and D014 the API is a *thin interface*: it wires HTTP to the engine
and contains no business logic of its own. Everything that isn't "receive,
delegate, respond" is delegated — auth to apps/api/telegram.py, model
selection and generation to core/, outbound to apps/api/telegram.py.

Per D016 the handler is synchronous: the request handler calls the model and
replies inline. Background execution is Milestone F. The known consequence
is that a model call slower than Telegram's webhook timeout (~seconds) risks
a retry that produces a duplicate reply. Recorded as an open risk.

The module-level `app = create_app(load_api_settings())` exists so uvicorn's
documented entry point works:

    uvicorn apps.api.app:app

`sys.path.insert(...)` at the top mirrors `apps/cli/main.py` — it lets
`apps.api` reach `core.*` when the app is loaded by path from the repo root.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import requests
from fastapi import FastAPI, Request

from apps.api.settings import ApiSettings, load_api_settings
from apps.api.telegram import (
    TelegramSendError,
    is_authorized,
    parse_update,
    send_message,
)
from core.config import Settings
from core.models.exceptions import ModelError
from core.models.registry import build_default_registry
from core.models.retry import generate_with_retry
from core.models.routing import DEFAULT_TASK_TYPE, route

logger = logging.getLogger("apps.api.app")

# The header Telegram sends when the webhook was registered with a secret.
# Lower-cased because HTTP headers are case-insensitive and Starlette
# normalizes them.
WEBHOOK_SECRET_HEADER = "x-telegram-bot-api-secret-token"


def create_app(
    settings: ApiSettings,
    *,
    registry_builder: Callable[[Settings], Any] = build_default_registry,
    http: Any = requests,
) -> FastAPI:
    """Build the API app against explicit settings.

    `registry_builder` and `http` are injectable so tests can exercise the
    full webhook path against fakes — no network, no keys, no live model.
    Defaults are the real things, matching the injection pattern used by
    `apps/cli/main.py` and `core/models/retry.py`.

    Settings, the registry builder, and the http client are stored on
    `app.state` so the handler reaches them via `request.app.state` without
    module globals.
    """
    app = FastAPI(title="Personal AI OS — Cloud API", version="0.1.0")
    app.state.settings = settings
    app.state.registry_builder = registry_builder
    app.state.http = http

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/telegram/webhook")
    async def telegram_webhook(request: Request, payload: dict) -> dict[str, bool]:
        """Receive a Telegram update and reply through the engine.

        Every failure branch returns `{"ok": True}` with status 200 — the
        response tells Telegram the push was received and not to retry, and
        the uniform body means the response does not leak which branch was
        taken (destination §11). The only branch that calls send_message is:
        correct secret header, parseable update, authorized user, model
        returned text, outbound succeeded.
        """
        current: ApiSettings = request.app.state.settings

        # 1. Secret header — cheapest check, rejects random POSTs before any
        #    body work. Constant-time comparison is not necessary here: the
        #    secret is high-entropy and the header value is not attacker-
        #    controlled in a way that would benefit from timing analysis.
        provided = request.headers.get(WEBHOOK_SECRET_HEADER, "")
        if not current.telegram_webhook_secret or provided != current.telegram_webhook_secret:
            logger.info("webhook: rejected (bad or missing secret header)")
            return {"ok": True}

        # 2. Parse — non-message updates, edits, empty text, malformed
        #    payloads all return None and are ignored silently.
        incoming = parse_update(payload)
        if incoming is None:
            logger.info("webhook: ignored (no parseable text message)")
            return {"ok": True}

        # 3. Allowlist — reject silently. Do not log the user_id (would leak
        #    "someone tried"); log only the fact of rejection.
        if not is_authorized(incoming.user_id, current):
            logger.info(
                "webhook: rejected (unauthorized) update_id=%s", incoming.update_id
            )
            return {"ok": True}

        # 4. Engine — routing -> registry -> generate_with_retry, same chain
        #    as apps/cli/main.py. A ModelError after retries is logged and
        #    swallowed; we do not reply on failure (deferred to a later
        #    milestone to decide user-facing error messages).
        logical_model = route(DEFAULT_TASK_TYPE, current.engine.model_policy)
        try:
            registry = request.app.state.registry_builder(current.engine)
            result = generate_with_retry(
                registry,
                incoming.text,
                primary=logical_model,
                fallback=current.engine.model_fallback or None,
            )
        except ModelError as exc:
            logger.warning(
                "webhook: model failure for update_id=%s: %s: %s",
                incoming.update_id,
                type(exc).__name__,
                exc,
            )
            return {"ok": True}

        # 5. Outbound — a send failure is logged and swallowed; the webhook
        #    still returns 200 so Telegram does not retry (which would
        #    duplicate the model call we already made).
        try:
            send_message(
                incoming.chat_id,
                result.text,
                current,
                http=request.app.state.http,
            )
        except TelegramSendError as exc:
            logger.warning(
                "webhook: send failure for update_id=%s: %s",
                incoming.update_id,
                exc,
            )
            return {"ok": True}

        logger.info(
            "webhook: replied update_id=%s logical=%s provider=%s model=%s",
            incoming.update_id,
            logical_model,
            result.provider,
            result.model,
        )
        return {"ok": True}

    return app


# uvicorn entry point: `uvicorn apps.api.app:app`
app = create_app(load_api_settings())
