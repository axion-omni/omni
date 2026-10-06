"""
apps/api/app.py — FastAPI cloud API (Milestone D).

First brick: a running app with a health check, built as an app factory so
tests can construct it against injected settings (the same discipline
`apps/cli/main.py` uses for its `settings_loader` / `registry_builder`).

Per D003 and D014 the API is a *thin interface*: it wires HTTP to the engine
and contains no business logic of its own. Per the handoff, nothing in this
package imports a Telegram client or touches the model pipeline in D1 — that
arrives in D2 (parsing/auth), D3 (outbound), D4 (end-to-end wiring).

The module-level `app = create_app(load_api_settings())` exists so uvicorn's
documented entry point works:

    uvicorn apps.api.app:app

`sys.path.insert(...)` at the top mirrors `apps/cli/main.py` — it lets
`apps.api` reach `core.*` when the app is loaded by path from the repo root.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI

from apps.api.settings import ApiSettings, load_api_settings


def create_app(settings: ApiSettings) -> FastAPI:
    """Build the API app against explicit settings.

    Settings are stored on `app.state.settings` so handlers (from D4 onward)
    can reach them via `request.app.state.settings` without a module global.
    """
    app = FastAPI(title="Personal AI OS — Cloud API", version="0.1.0")
    app.state.settings = settings

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# uvicorn entry point: `uvicorn apps.api.app:app`
app = create_app(load_api_settings())
