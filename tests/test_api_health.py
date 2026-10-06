"""
Tests for apps/api/app.py — D1 health check.

Injection discipline matches tests/test_cli.py: a real `core.config.Settings`
with `"fake"` credentials (no env, no network, no keys) wrapped in an
`ApiSettings`, then `create_app(api_settings)` built explicitly for the test.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app import create_app
from apps.api.settings import ApiSettings
from core.config import Settings


def _fake_engine_settings() -> Settings:
    """Mirror tests/test_cli.py::_fake_settings — real dataclass, fake creds."""
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
        model_fallback="",
    )


def _fake_api_settings() -> ApiSettings:
    return ApiSettings(engine=_fake_engine_settings())


def test_health_returns_ok():
    app = create_app(_fake_api_settings())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_level_app_is_wired():
    """The uvicorn entry point (`uvicorn apps.api.app:app`) must exist and
    serve /health without any test-side construction."""
    import apps.api.app as app_module

    assert isinstance(app_module.app, FastAPI)

    client = TestClient(app_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
