"""
core/memory/constitution.py

Session 8 brick (Milestone C): the Constitution repository.

The single interface the rest of the system uses to read and write Project
Constitutions. Above this file, nothing knows or cares that the store is
PostgreSQL — the repository hides it (Part XXII: swappable storage).

Rules this file enforces, non-negotiably:
  - Append-only, versioned (D010). Every change writes a NEW row at
    version = latest + 1. No row is ever UPDATEd or DELETEd by this layer.
  - Per-project scoped. Every query filters by project_id, so one project's
    memory can never leak into another's (destination architecture §11).
  - No silent failure. A missing project raises ConstitutionNotFoundError,
    never returns None. A commit failure propagates. A read that expects one
    row and gets zero raises.

The Postgres driver is not imported here — all access is through
core.memory.db.connect(), which owns the driver import (D002 generalized;
D009). That keeps the storage engine swappable to a different backend with
no change to this file's callers.

Note on `_next_version`: the +1 is computed in Python, not in SQL. The SQL
returns the raw MAX; the repository adds one. That keeps the fake connection
in tests honest (a fake Postgres returns what Postgres returns), and it is
the seam where a retry-on-conflict (UNIQUE violation under concurrent
writers) will land at Milestone F, when multiple workers exist.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from core.config import Settings
from core.memory.db import connect
from core.memory.exceptions import ConstitutionNotFoundError
from core.memory.models import Constitution

logger = logging.getLogger(__name__)


class ConstitutionRepository:
    """Read/write access to Project Constitutions, append-only and versioned.

    Construction: pass the loaded Settings and (optionally) a connector so
    tests and non-Postgres backends can inject their own connection factory.
    If no connector is given, core.memory.db.connect's default psycopg path is
    used.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        connector: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self._settings = settings
        self._connector = connector

    # --- public API -------------------------------------------------------

    def create(
        self,
        name: str,
        constitution: Optional[Constitution] = None,
    ) -> str:
        """Create a new project and its first Constitution version.

        Returns the generated project_id (a uuid string). `constitution`
        defaults to an empty Constitution (all fields blank), so a project can
        be started before intake is complete — matching the model's design.
        """
        if not name or not name.strip():
            # Refuse early with a Python-level error, not a DB constraint error
            # later. Rigid, and clear to the caller.
            raise ValueError("Project name must be a non-empty string.")

        c = constitution or Constitution()
        conn = connect(self._settings, connector=self._connector)
        try:
            project_id = self._insert_project(conn, name)
            self._insert_constitution(conn, project_id, 1, c)
            conn.commit()
            logger.info("created constitution project_id=%s v1", project_id)
            return project_id
        finally:
            self._close(conn)

    def get(self, project_id: str) -> Constitution:
        """Return the latest Constitution for the project.

        Raises ConstitutionNotFoundError if the project has no Constitution.
        Never returns None.
        """
        conn = connect(self._settings, connector=self._connector)
        try:
            row = self._select_latest(conn, project_id)
        finally:
            self._close(conn)

        if row is None:
            logger.warning("constitution not found project_id=%s", project_id)
            raise ConstitutionNotFoundError(
                f"No Constitution found for project_id={project_id!r}."
            )
        return Constitution.model_validate(row)

    def get_version(self, project_id: str, version: int) -> Constitution:
        """Return a specific historical version of the project's Constitution."""
        conn = connect(self._settings, connector=self._connector)
        try:
            row = self._select_version(conn, project_id, version)
        finally:
            self._close(conn)

        if row is None:
            logger.warning(
                "constitution version not found project_id=%s version=%s",
                project_id,
                version,
            )
            raise ConstitutionNotFoundError(
                f"No Constitution v{version} for project_id={project_id!r}."
            )
        return Constitution.model_validate(row)

    def append_change(
        self,
        project_id: str,
        change: str,
        **field_updates: Any,
    ) -> int:
        """Append a new version of the project's Constitution.

        `change` is a short human description of what changed; it is appended
        to change_history. `field_updates` are keyword updates to any of the
        12 other Constitution fields (e.g. success_criteria=[...]). Returns
        the new version number.
        """
        conn = connect(self._settings, connector=self._connector)
        try:
            current = self._select_latest(conn, project_id)
            if current is None:
                logger.warning(
                    "append_change on unknown project_id=%s", project_id
                )
                raise ConstitutionNotFoundError(
                    f"Cannot append change: no Constitution for project_id={project_id!r}."
                )

            new_version_number = self._next_version(conn, project_id)
            updated = self._apply_change(current, change, field_updates)

            self._insert_constitution(
                conn, project_id, new_version_number, updated
            )
            conn.commit()
            logger.info(
                "appended constitution change project_id=%s v%s",
                project_id,
                new_version_number,
            )
            return new_version_number
        finally:
            self._close(conn)

    def history(self, project_id: str) -> list[tuple[int, datetime]]:
        """Return [(version, created_at), ...] for the project, ordered ascending.

        No content is loaded — this is a lightweight index, useful for
        displaying "v3, 2 minutes ago; v4, just now" in a UI.
        """
        conn = connect(self._settings, connector=self._connector)
        try:
            rows = self._select_history(conn, project_id)
        finally:
            self._close(conn)

        if not rows:
            logger.warning("history requested for unknown project_id=%s", project_id)
            raise ConstitutionNotFoundError(
                f"No Constitution history for project_id={project_id!r}."
            )
        return [(int(v), ts) for v, ts in rows]

    # --- SQL primitives (one per operation; easy to audit) ----------------

    def _insert_project(self, conn: Any, name: str) -> str:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects (name) VALUES (%s) RETURNING id",
                (name,),
            )
            row = cur.fetchone()
        if row is None:
            # A correct Postgres never does this with RETURNING. If it does,
            # something is deeply wrong — fail loudly.
            raise RuntimeError("INSERT ... RETURNING id returned no row.")
        return str(row[0])

    def _insert_constitution(
        self,
        conn: Any,
        project_id: str,
        version: int,
        constitution: Constitution,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO constitutions (project_id, version, content) "
                "VALUES (%s, %s, %s)",
                (project_id, version, constitution.model_dump_json()),
            )

    def _select_latest(self, conn: Any, project_id: str) -> Optional[dict]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM constitutions "
                "WHERE project_id = %s ORDER BY version DESC LIMIT 1",
                (project_id,),
            )
            row = cur.fetchone()
        return self._row_content(row)

    def _select_version(
        self, conn: Any, project_id: str, version: int
    ) -> Optional[dict]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM constitutions "
                "WHERE project_id = %s AND version = %s",
                (project_id, version),
            )
            row = cur.fetchone()
        return self._row_content(row)

    def _select_history(
        self, conn: Any, project_id: str
    ) -> list[tuple[int, datetime]]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version, created_at FROM constitutions "
                "WHERE project_id = %s ORDER BY version ASC",
                (project_id,),
            )
            return list(cur.fetchall())

    def _next_version(self, conn: Any, project_id: str) -> int:
        """Return the next version number = current MAX(version) + 1.

        The SQL returns the raw MAX (0 if the project has no versions yet);
        the +1 is computed here in Python. See the module docstring for why.
        """
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(version), 0) FROM constitutions "
                "WHERE project_id = %s",
                (project_id,),
            )
            row = cur.fetchone()
        if row is None or row[0] is None:
            raise RuntimeError("MAX(version) query returned no row.")
        return int(row[0]) + 1

    # --- helpers ----------------------------------------------------------

    @staticmethod
    def _row_content(row: Optional[Iterable[Any]]) -> Optional[dict]:
        """Extract the `content` jsonb from a single-column row, or None.

        psycopg returns jsonb as a Python dict already; a fake connector in
        tests returns whatever it was told to. We accept a dict directly and
        also a JSON string (defensive, in case a driver variant hands back
        text) — but never invent content. If the shape is unrecognized we
        return None, which the caller turns into a hard error.
        """
        if row is None:
            return None
        value = row[0]
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None

    @staticmethod
    def _apply_change(
        current: dict,
        change: str,
        field_updates: dict,
    ) -> Constitution:
        """Build the next Constitution from the current one plus the change.

        Rules:
          - Any field in `field_updates` must be a real Constitution field,
            else ValueError (rigid; typos must not silently no-op).
          - change_history is always appended (never replaced).
          - All other fields are carried over.
        """
        allowed = set(Constitution.model_fields.keys())
        bad = set(field_updates) - allowed
        if bad:
            raise ValueError(
                f"Unknown Constitution field(s) in field_updates: {sorted(bad)}"
            )
        if "change_history" in field_updates:
            raise ValueError(
                "change_history is owned by the repository; pass `change` instead."
            )

        updated = Constitution.model_validate({**current, **field_updates})
        updated = updated.model_copy(
            update={"change_history": [*updated.change_history, change]}
        )
        return updated

    @staticmethod
    def _close(conn: Any) -> None:
        close = getattr(conn, "close", None)
        if callable(close):
            close()
