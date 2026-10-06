"""
Tests for core.memory.constitution — the Constitution repository.

Level-2 discipline: everything here runs with no Postgres driver installed
and no database reachable, using an injected fake connection that records
SQL and returns canned rows. The one live test at the bottom SKIPS unless
DATABASE_URL is set — that's an operator level-3 step, deliberately not part
of the mocked suite.

What is proven here (the Session 8 acceptance criterion):
  - create -> get round-trips a Constitution, in a fresh repository instance
    (persistence across instances, not just across calls).
  - append_change writes a NEW row at version = latest + 1 and leaves the
    previous version intact (append-only, D010).
  - a missing project raises ConstitutionNotFoundError, never returns None.
  - field_updates apply; unknown field names are rejected; change_history
    cannot be set directly.

Design note (Session 8): the fake Postgres returns the RAW MAX(version) — the
repository adds 1 in Python. That is why `program(rows=[..., (3,)])` produces
version 4, and `program(rows=[..., (1,)])` produces version 2. The fake
models what Postgres actually returns; the arithmetic is the repository's.
"""

from __future__ import annotations

import os

import pytest

from core.config import Settings
from core.memory.constitution import ConstitutionRepository
from core.memory.exceptions import ConstitutionNotFoundError
from core.memory.models import Constitution


# --- shared helpers -------------------------------------------------------

def _settings(database_url: str = "postgresql://fake/fake") -> Settings:
    # Non-empty DATABASE_URL so connect() doesn't fail before the fake
    # connector is even used.
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
    """Records executed SQL + params; returns rows from a program list."""

    def __init__(self, conn: "_FakeConn"):
        self._conn = conn
        self._last_sql = ""
        self._last_params: tuple = ()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._last_sql = " ".join(sql.split())  # collapse whitespace for matching
        self._last_params = tuple(params or ())
        self._conn.executed.append((self._last_sql, self._last_params))

    def fetchone(self):
        return self._conn.next_row()

    def fetchall(self):
        return self._conn.next_all()


class _FakeConn:
    """A tiny programmable in-memory Postgres for the repository's call set."""

    def __init__(self):
        self.executed: list[tuple[str, tuple]] = []
        self.committed = 0
        self.closed = False
        self._rows: list = []  # queue of results for fetchone
        self._all: list = []   # result for the next fetchall
        self._next_project_id = "11111111-1111-1111-1111-111111111111"

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        self.committed += 1

    def close(self):
        self.closed = True

    # programmable return values -------------------------------------------
    def program(self, *, rows=None, all_rows=None, project_id=None):
        if rows is not None:
            self._rows = list(rows)
        if all_rows is not None:
            self._all = list(all_rows)
        if project_id is not None:
            self._next_project_id = project_id
        return self

    def next_row(self):
        if not self._rows:
            return None
        return self._rows.pop(0)

    def next_all(self):
        return self._all


def _fake_connector(conn: _FakeConn):
    return lambda url: conn


def _repository(conn: _FakeConn) -> ConstitutionRepository:
    return ConstitutionRepository(_settings(), connector=_fake_connector(conn))


# --- create ---------------------------------------------------------------

def test_create_inserts_project_then_constitution_and_returns_uuid():
    conn = _FakeConn().program(rows=[("my-uuid-here",)])
    repo = _repository(conn)

    project_id = repo.create("C-Transit", Constitution(mission="offline tap-to-ride"))

    assert project_id == "my-uuid-here"
    # Order: project insert, then constitution insert.
    sqls = [s for s, _ in conn.executed]
    assert any("INSERT INTO projects" in s for s in sqls)
    assert any("INSERT INTO constitutions" in s for s in sqls)
    assert sqls.index(next(s for s in sqls if "INSERT INTO projects" in s)) < \
           sqls.index(next(s for s in sqls if "INSERT INTO constitutions" in s))
    # The project insert used RETURNING id (not a client-generated id).
    assert any("RETURNING id" in s for s in sqls)
    assert conn.committed == 1
    assert conn.closed is True


def test_create_defaults_to_empty_constitution():
    conn = _FakeConn().program(rows=[("pid",)])
    repo = _repository(conn)

    repo.create("Empty project")

    # The constitution INSERT's params should carry the JSON of an empty model.
    insert_calls = [p for s, p in conn.executed if "INSERT INTO constitutions" in s]
    assert insert_calls, "no constitution INSERT was issued"
    _, _, content_json = insert_calls[0]
    assert Constitution.model_validate_json(content_json) == Constitution()


def test_create_rejects_blank_name_before_touching_the_db():
    conn = _FakeConn()
    repo = _repository(conn)

    with pytest.raises(ValueError):
        repo.create("   ")

    assert conn.executed == []  # nothing was sent to the database


# --- get ------------------------------------------------------------------

def test_get_returns_the_latest_version_as_a_constitution():
    conn = _FakeConn().program(
        rows=[({"mission": "m", "change_history": ["v1"]},)]
    )
    repo = _repository(conn)

    result = repo.get("pid")

    assert isinstance(result, Constitution)
    assert result.mission == "m"
    assert result.change_history == ["v1"]
    # It must have asked for the latest (ORDER BY version DESC LIMIT 1).
    sqls = [s for s, _ in conn.executed]
    assert any("ORDER BY version DESC" in s for s in sqls)
    assert conn.closed is True


def test_get_raises_when_no_constitution_exists():
    conn = _FakeConn().program(rows=[])  # no rows at all
    repo = _repository(conn)

    with pytest.raises(ConstitutionNotFoundError):
        repo.get("ghost-project")

    assert conn.closed is True  # even on the raise path, we close cleanly


# --- get_version ----------------------------------------------------------

def test_get_version_targets_a_specific_version():
    conn = _FakeConn().program(rows=[({"mission": "old"},)])
    repo = _repository(conn)

    result = repo.get_version("pid", 2)

    assert result.mission == "old"
    sqls = [s for s, _ in conn.executed]
    assert any("version = %s" in s for s in sqls)
    # And the version param was threaded through:
    params = [p for s, p in conn.executed if "version = %s" in s]
    assert any(p == ("pid", 2) for p in params)


def test_get_version_raises_when_the_version_does_not_exist():
    conn = _FakeConn().program(rows=[])
    repo = _repository(conn)
    with pytest.raises(ConstitutionNotFoundError):
        repo.get_version("pid", 99)


# --- append_change --------------------------------------------------------

def test_append_change_writes_a_new_row_at_next_version():
    # First read: latest content (latest version is 3).
    # Second read: MAX(version) = 3 — the repository adds 1 → new version 4.
    conn = _FakeConn().program(
        rows=[({"mission": "m", "change_history": ["v1", "v2", "v3"]},), (3,)]
    )
    repo = _repository(conn)

    new_version = repo.append_change("pid", "v4: added constraints")

    assert new_version == 4
    inserts = [p for s, p in conn.executed if "INSERT INTO constitutions" in s]
    assert inserts, "no INSERT issued on append_change"
    project_id, version, content_json = inserts[0]
    assert project_id == "pid"
    assert version == 4
    updated = Constitution.model_validate_json(content_json)
    assert updated.change_history == ["v1", "v2", "v3", "v4: added constraints"]
    assert conn.committed == 1


def test_append_change_applies_field_updates():
    # MAX(version) = 1; repository adds 1 → new version 2.
    conn = _FakeConn().program(
        rows=[({"mission": "m"},), (1,)]
    )
    repo = _repository(conn)

    new_version = repo.append_change(
        "pid", "v2: added criteria", success_criteria=["fast", "offline-capable"]
    )

    assert new_version == 2
    insert_params = [p for s, p in conn.executed if "INSERT INTO constitutions" in s][0]
    content_json = insert_params[2]
    updated = Constitution.model_validate_json(content_json)
    assert updated.success_criteria == ["fast", "offline-capable"]
    assert updated.mission == "m"  # untouched fields carried over


def test_append_change_rejects_unknown_field_names():
    conn = _FakeConn().program(rows=[({"mission": "m"},), (1,)])
    repo = _repository(conn)
    with pytest.raises(ValueError):
        repo.append_change("pid", "typo", sucess_criteria=["x"])  # misspelled


def test_append_change_refuses_to_take_change_history_directly():
    conn = _FakeConn().program(rows=[({"mission": "m"},), (1,)])
    repo = _repository(conn)
    with pytest.raises(ValueError):
        repo.append_change("pid", "x", change_history=["y"])


def test_append_change_raises_when_project_unknown():
    conn = _FakeConn().program(rows=[])  # latest read returns nothing
    repo = _repository(conn)
    with pytest.raises(ConstitutionNotFoundError):
        repo.append_change("ghost", "v2")


# --- history --------------------------------------------------------------

def test_history_returns_versions_in_ascending_order():
    from datetime import datetime, timezone

    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2025, 1, 2, tzinfo=timezone.utc)
    conn = _FakeConn().program(all_rows=[(1, t1), (2, t2)])
    repo = _repository(conn)

    rows = repo.history("pid")

    assert rows == [(1, t1), (2, t2)]
    sqls = [s for s, _ in conn.executed]
    assert any("ORDER BY version ASC" in s for s in sqls)


def test_history_raises_when_project_unknown():
    conn = _FakeConn().program(all_rows=[])
    repo = _repository(conn)
    with pytest.raises(ConstitutionNotFoundError):
        repo.history("ghost")


# --- live integration (level 3) -------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="no DATABASE_URL — live repository round-trip is a level-3 step",
)
def test_live_create_get_round_trip_across_repository_instances():
    """Real Postgres: create in one repo, read in a fresh one. This is the
    Milestone C proof that state survives a process boundary."""
    url = os.environ["DATABASE_URL"]
    settings = _settings(url)
    repo1 = ConstitutionRepository(settings)
    project_id = repo1.create("L3 project", Constitution(mission="persisted"))

    repo2 = ConstitutionRepository(settings)
    fetched = repo2.get(project_id)
    assert fetched.mission == "persisted"

    new_v = repo2.append_change(project_id, "v2: amend", purpose="prove append")
    assert new_v == 2
    latest = repo2.get(project_id)
    assert latest.purpose == "prove append"
    assert latest.change_history[-1] == "v2: amend"
