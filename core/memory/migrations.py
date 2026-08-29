"""
core/memory/migrations.py

Session 7 brick (Milestone C): a minimal forward-only migration runner.

Deliberately not Alembic — plain .sql files in infra/migrations/ applied in
lexical order, with applied versions tracked in a `schema_migrations` table
(D010: smallest dependency surface, explicit SQL, matches the project's
no-ceremony ethos). A different backend or a real migration tool later is a
localized change (Part XXII).

The pure parts — discovering migration files and computing which are pending —
are unit-tested with no database. Actually applying them touches Postgres and is
covered by a test that SKIPS without DATABASE_URL (operator level-3).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from core.config import Settings, load_settings
from core.memory.db import connect

# Repo-root/infra/migrations — this module is core/memory/migrations.py, so
# parents[2] is the repo root.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "infra" / "migrations"

_MIGRATIONS_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations ("
    "version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
)


@dataclass(frozen=True)
class Migration:
    version: str  # filename stem, e.g. "0001_init"
    path: Path


def discover_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Return all .sql migrations, sorted by version (lexical = chronological
    given zero-padded numeric prefixes)."""
    if not migrations_dir.is_dir():
        return []
    files = sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)
    return [Migration(version=p.stem, path=p) for p in files]


def pending(migrations: list[Migration], applied: set[str]) -> list[Migration]:
    """Pure: the migrations not yet applied, preserving order."""
    return [m for m in migrations if m.version not in applied]


def _split_statements(sql: str) -> list[str]:
    """Split a simple DDL script into statements. Our migrations contain no
    function bodies or embedded semicolons, so splitting on ';' is safe."""
    return [s.strip() for s in sql.split(";") if s.strip()]


def _applied_versions(conn: Any) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(_MIGRATIONS_TABLE_SQL)
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _apply_one(conn: Any, migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        for statement in _split_statements(sql):
            cur.execute(statement)
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)",
            (migration.version,),
        )


def run(
    settings: Optional[Settings] = None,
    *,
    connector: Optional[Callable[[str], Any]] = None,
    migrations_dir: Path = MIGRATIONS_DIR,
) -> list[str]:
    """Apply all pending migrations against the configured database.

    Returns the list of versions applied this run (empty if already current).
    Raises DatabaseNotConfiguredError / DatabaseConnectionError via connect().
    Each migration + its schema_migrations insert commit together.
    """
    settings = settings or load_settings()
    conn = connect(settings, connector=connector)
    try:
        applied = _applied_versions(conn)
        to_apply = pending(discover_migrations(migrations_dir), applied)
        done: list[str] = []
        for migration in to_apply:
            _apply_one(conn, migration)
            commit = getattr(conn, "commit", None)
            if callable(commit):
                commit()
            done.append(migration.version)
        return done
    finally:
        close = getattr(conn, "close", None)
        if callable(close):
            close()
