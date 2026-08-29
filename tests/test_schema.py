"""
Tests for the persistence schema (Session 7): the Constitution model and the
migration runner. Level-2 discipline — no database and no driver needed. The
pure logic (model round-trip, migration discovery/pending) is tested directly;
applying migrations is tested against an injected fake connection, and the fully
live apply SKIPS unless DATABASE_URL is set.
"""

from __future__ import annotations

import os

import pytest

from core.config import Settings
from core.memory.migrations import (
    MIGRATIONS_DIR,
    Migration,
    discover_migrations,
    pending,
    run,
)
from core.memory.models import Constitution


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


# --- Constitution model ----------------------------------------------------

def test_constitution_has_the_thirteen_sections():
    c = Constitution()
    expected = {
        "mission", "purpose", "desired_outcome", "success_criteria",
        "constraints", "assumptions", "non_negotiables", "available_resources",
        "known_facts", "unknowns", "risks", "decisions", "change_history",
    }
    assert set(c.model_dump().keys()) == expected


def test_constitution_defaults_are_empty():
    c = Constitution()
    assert c.mission == ""
    assert c.success_criteria == []
    assert c.change_history == []


def test_constitution_json_round_trip():
    c = Constitution(
        mission="Win the scholarship",
        success_criteria=["submitted before deadline"],
        change_history=["v1: created"],
    )
    restored = Constitution.model_validate_json(c.model_dump_json())
    assert restored == c


# --- migration discovery / pending (pure) ----------------------------------

def test_discover_finds_the_initial_migration():
    versions = [m.version for m in discover_migrations()]
    assert "0001_init" in versions
    # sorted ascending
    assert versions == sorted(versions)
    assert (MIGRATIONS_DIR / "0001_init.sql").exists()


def test_pending_filters_already_applied():
    migs = [Migration("0001_init", MIGRATIONS_DIR / "0001_init.sql"),
            Migration("0002_next", MIGRATIONS_DIR / "0002_next.sql")]
    assert [m.version for m in pending(migs, {"0001_init"})] == ["0002_next"]
    assert pending(migs, {"0001_init", "0002_next"}) == []


# --- runner against a fake connection (no DB) ------------------------------

class _FakeCursor:
    def __init__(self, store):
        self._store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._store["executed"].append(sql.strip().split("\n")[0])
        self._last = sql

    def fetchall(self):
        # pretend nothing has been applied yet
        return []


class _FakeConn:
    def __init__(self):
        self.store = {"executed": []}
        self.committed = 0
        self.closed = False

    def cursor(self):
        return _FakeCursor(self.store)

    def commit(self):
        self.committed += 1

    def close(self):
        self.closed = True


def test_run_applies_pending_against_fake_connection():
    conn = _FakeConn()
    applied = run(_settings("postgresql://x/y"), connector=lambda url: conn)

    assert "0001_init" in applied
    assert conn.committed >= 1
    assert conn.closed is True
    # the schema_migrations bookkeeping ran
    joined = " ".join(conn.store["executed"]).lower()
    assert "schema_migrations" in joined


@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="no DATABASE_URL — live migration apply is a level-3 step",
)
def test_run_against_live_database_is_idempotent():
    # Operator level-3: applies 0001 to a real Postgres, then a second run is a
    # no-op (already recorded in schema_migrations).
    s = _settings(os.environ["DATABASE_URL"])
    run(s)
    assert run(s) == []
