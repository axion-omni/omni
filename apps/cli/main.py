"""
apps/cli/main.py

Session 2 brick: first end-to-end run from a terminal command.

Deliberately thin — this is an interface, not intelligence. Per
SYSTEM_ARCHITECTURE.md's standing rule (and Part XV of the destination
architecture), no logic lives here that `core/` doesn't own. This file's
only job is: read input, call core, print output.

Usage:
    python apps/cli/main.py "your prompt here"
    python apps/cli/main.py "your prompt" --model cheap-fast   # once the
        Session 3 registry exists; ignored today if passed early.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import load_settings
from core.models.exceptions import ModelError
from core.models.factory import get_active_provider


def run(argv: list[str], provider_factory=get_active_provider, settings_loader=load_settings) -> int:
    """
    provider_factory / settings_loader are injectable so tests can run this
    against a fake provider without touching env vars or the network —
    same pattern used throughout core/models.
    """
    if len(argv) < 2 or not argv[1].strip():
        print("Usage: python apps/cli/main.py \"<prompt>\"", file=sys.stderr)
        return 1

    prompt = argv[1]
    settings = settings_loader()

    try:
        provider = provider_factory(settings)
        result = provider.generate(prompt)
    except ModelError as exc:
        print(f"Error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    print(result.text)
    print(
        f"[{result.provider}/{result.model} — {result.input_tokens} in / "
        f"{result.output_tokens} out tokens]",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv))
