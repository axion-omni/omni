"""
infra/migrate.py

Thin CLI wrapper around core.memory.migrations. Run it to apply all pending
database migrations against the configured DATABASE_URL:

    python infra/migrate.py

Local dev first:
    docker compose -f infra/docker-compose.yml up -d
    # set DATABASE_URL in .env
    python infra/migrate.py

The logic lives in core/memory/migrations.py (importable + unit-tested); this
file only wires argv -> that runner and prints a human-readable result.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import load_settings
from core.memory.exceptions import MemoryError as _MemoryError
from core.memory.migrations import run


def main() -> int:
    try:
        applied = run(load_settings())
    except _MemoryError as exc:
        print(f"Migration failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    if applied:
        print("Applied migrations: " + ", ".join(applied))
    else:
        print("Database already up to date; nothing to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
