"""
core/memory/db.py

Session 6 brick (Milestone C): the database access seam.

One place that turns a DATABASE_URL into a live PostgreSQL connection. Nothing
else in the system imports the Postgres driver directly — same rule the model
layer applies to provider SDKs (D002, generalized). That keeps the storage
engine swappable (Master Construction Spec, Part XXII): a different backend is a
change here, not in every repository.

The `psycopg` import is lazy (inside the connector), exactly like
AnthropicProvider's SDK import — so the unit tests run with the driver absent
and no live database, and `pytest` stays green with zero infrastructure. The one
live check (`ping`) is exercised by a test that SKIPS when DATABASE_URL is unset.

Credential safety (post-S8 incident, D013): every driver error message is
redacted before it becomes a DatabaseConnectionError, AND the original
exception's args are redacted in place so the chained `__cause__` traceback
cannot re-leak the URL. The redaction logic lives in core.config so Settings
and the db seam share one source of truth.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from core.config import Settings, redact_credentials
from core.memory.exceptions import (
    DatabaseConnectionError,
    DatabaseNotConfiguredError,
)


def _default_connector(database_url: str) -> Any:
    """Open a real psycopg connection. Imported lazily so tests never need the
    driver installed or a database reachable."""
    import psycopg  # noqa: PLC0415 — intentional lazy import, see module docstring

    return psycopg.connect(database_url)


def _sanitize(exc: BaseException) -> None:
    """Best-effort: redact the exception's own message in place so any
    chained traceback (via `raise ... from exc`) prints a redacted version.
    Some exceptions don't allow args mutation; we never fail because of that.
    """
    try:
        msg = str(exc)
        redacted = redact_credentials(msg)
        if redacted != msg:
            exc.args = (redacted,)
    except Exception:
        # Never let a sanitization failure mask the real error.
        pass


def connect(
    settings: Settings,
    *,
    connector: Optional[Callable[[str], Any]] = None,
) -> Any:
    """Return a live database connection for the configured DATABASE_URL.

    `connector` is injectable so tests can supply a fake instead of a real
    psycopg connection — the same pattern as the model providers' client
    injection. Raises:
      - DatabaseNotConfiguredError if DATABASE_URL is empty (fail clearly).
      - DatabaseConnectionError if the driver fails to connect (message is
        redacted — no credential reaches the traceback).
    """
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set — no database configured. Set it in .env "
            "locally or the host secret manager in production."
        )

    connect_fn = connector or _default_connector
    try:
        return connect_fn(settings.database_url)
    except DatabaseNotConfiguredError:
        raise
    except Exception as exc:
        _sanitize(exc)
        raise DatabaseConnectionError(redact_credentials(str(exc))) from exc


def ping(
    settings: Settings,
    *,
    connector: Optional[Callable[[str], Any]] = None,
) -> bool:
    """Open a connection, run `SELECT 1`, and return True on success.

    The minimal "is the database actually reachable" health check. Raises
    DatabaseNotConfiguredError / DatabaseConnectionError on failure rather than
    returning False, so callers get a specific reason.
    """
    conn = connect(settings, connector=connector)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
        return bool(row and row[0] == 1)
    except (DatabaseNotConfiguredError, DatabaseConnectionError):
        raise
    except Exception as exc:
        _sanitize(exc)
        raise DatabaseConnectionError(redact_credentials(str(exc))) from exc
    finally:
        close = getattr(conn, "close", None)
        if callable(close):
            close()
