"""
Tests for core.memory.db — the database access seam.

Level-2 discipline: these stay green with no Postgres driver installed and no
database reachable. Config parsing and the connect/ping logic are tested with an
injected fake connector (same pattern as the model providers' client injection).
The one genuinely live check SKIPS unless DATABASE_URL is set — that's an
operator level-3 step, deliberately not part of the mocked suite.
"""

from __future__ import annotations

import os

import pytest

from core.config import Settings, load_settings
from core.memory.db import connect, ping
from core.memory.exceptions import (
    DatabaseConnectionError,
    DatabaseNotConfiguredError,
)


def _settings(database_url: str = "") -> Settings:
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="x",
        model_fallback="",
        database_url=database_url,
    )


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql):
        self.executed = sql

    def fetchone(self):
        return self._row


class _FakeConnection:
    def __init__(self, row=(1,)):
        self._row = row
        self.closed = False

    def cursor(self):
        return _FakeCursor(self._row)

    def close(self):
        self.closed = True


# --- config ---------------------------------------------------------------

def test_load_settings_reads_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    assert load_settings().database_url == "postgresql://u:p@localhost:5432/db"


def test_database_url_defaults_empty(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert load_settings().database_url == ""


# --- connect --------------------------------------------------------------

def test_connect_without_url_raises_not_configured():
    with pytest.raises(DatabaseNotConfiguredError):
        connect(_settings(""))


def test_connect_uses_injected_connector_with_the_url():
    seen = {}

    def fake_connector(url):
        seen["url"] = url
        return _FakeConnection()

    conn = connect(_settings("postgresql://x/y"), connector=fake_connector)

    assert seen["url"] == "postgresql://x/y"
    assert isinstance(conn, _FakeConnection)


def test_connect_translates_driver_error():
    def boom(url):
        raise RuntimeError("connection refused")

    with pytest.raises(DatabaseConnectionError):
        connect(_settings("postgresql://x/y"), connector=boom)


# --- ping -----------------------------------------------------------------

def test_ping_returns_true_and_closes_connection():
    conn = _FakeConnection(row=(1,))
    result = ping(_settings("postgresql://x/y"), connector=lambda url: conn)
    assert result is True
    assert conn.closed is True


def test_ping_without_url_raises_not_configured():
    with pytest.raises(DatabaseNotConfiguredError):
        ping(_settings(""))


@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="no DATABASE_URL — live DB ping is a level-3 step, not part of the mocked suite",
)
def test_ping_live_database():
    # Runs only when the operator has a real Postgres configured (their L3):
    #   docker compose -f infra/docker-compose.yml up -d
    assert ping(_settings(os.environ["DATABASE_URL"])) is True
