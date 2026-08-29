"""
Exceptions for the memory / persistence layer.

Mirrors the model layer's approach (core/models/exceptions.py): one base class
so nothing above this layer needs to know whether the backend is Postgres,
SQLite, or something else. Backend-specific driver errors get translated into
these before they escape the memory package.
"""


class MemoryError(Exception):
    """Base class for all persistence-layer errors."""


class DatabaseNotConfiguredError(MemoryError):
    """No DATABASE_URL is set. The caller asked for persistence but none is
    configured — fail clearly instead of silently connecting to nothing."""


class DatabaseConnectionError(MemoryError):
    """Could not connect to / reach the configured database."""
