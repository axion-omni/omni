"""
apps/cli/main.py

Session 2 brick, extended in Session 3: the terminal interface now resolves a
*logical* model name through the Model Registry instead of taking whatever the
active provider's default happens to be.

Deliberately thin — this is an interface, not intelligence. Per
SYSTEM_ARCHITECTURE.md's standing rule (and D003 / Section 3 of the destination
architecture), no logic lives here that `core/` doesn't own. This file's only
job is: read input, resolve + call core, print output.

Usage:
    python apps/cli/main.py "your prompt here"
    python apps/cli/main.py "your prompt" --model reasoning-strong
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import load_settings
from core.models.exceptions import ModelError
from core.models.registry import DEFAULT_LOGICAL_MODEL, build_default_registry

USAGE = 'Usage: python apps/cli/main.py "<prompt>" [--model <logical-name>]'


def _parse_args(argv: list[str]) -> tuple[str | None, str]:
    """Return (prompt, logical_model); prompt is None when it's missing.

    Hand-parsed rather than argparse on purpose: argparse runs its own
    sys.exit on bad input, which would fight run()'s clean int return contract
    that the tests rely on.
    """
    args = argv[1:]
    logical_model = DEFAULT_LOGICAL_MODEL

    if "--model" in args:
        i = args.index("--model")
        if i + 1 >= len(args):
            return None, logical_model  # --model with no value -> show usage
        logical_model = args[i + 1]
        del args[i : i + 2]

    prompt = args[0] if args and args[0].strip() else None
    return prompt, logical_model


def run(
    argv: list[str],
    registry_builder=build_default_registry,
    settings_loader=load_settings,
) -> int:
    """
    registry_builder / settings_loader are injectable so tests can run this
    against a fake registry without touching env vars or the network — the same
    injection pattern used throughout core/models.
    """
    prompt, logical_model = _parse_args(argv)
    if prompt is None:
        print(USAGE, file=sys.stderr)
        return 1

    settings = settings_loader()

    try:
        registry = registry_builder(settings)
        provider, model_id = registry.resolve(logical_model)
        result = provider.generate(prompt, model=model_id)
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
