"""
Exceptions for the memory / persistence layer.

Mirrors the model layer's approach (core/models/exceptions.py): one base class
so nothing above this layer needs to know whether the backend is Postgres,
SQLite, or something else. Backend-specific driver errors get translated into
these before they escape the memory package.

No-silent-failure contract (S8):
  - A read that finds nothing raises. It never returns None to mean "not found".
  - A write that cannot commit raises. It never swallows the failure.
  - All errors are subclasses of MemoryError, so callers can catch one type.
"""


class MemoryError(Exception):
    """Base class for all persistence-layer errors."""


class DatabaseNotConfiguredError(MemoryError):
    """No DATABASE_URL is set. The caller asked for persistence but none is
    configured — fail clearly instead of silently connecting to nothing."""


class DatabaseConnectionError(MemoryError):
    """Could not connect to / reach the configured database."""


class ConstitutionNotFoundError(MemoryError):
    """No Constitution exists for the given project (or version).

    Raised by ConstitutionRepository.get / get_version / append_change rather
    than returning None, so a missing project can never be silently treated as
    an empty one.
    """
