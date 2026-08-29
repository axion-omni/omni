"""
apps/cli/main.py

Session 2 brick, extended in Sessions 3–4: the terminal interface resolves a
*logical* model name through the Model Registry, choosing that name by
MODEL_POLICY (Session 4 routing) unless an explicit --model overrides it.

Deliberately thin — this is an interface, not intelligence. Per
SYSTEM_ARCHITECTURE.md's standing rule (and D003 / Section 3 of the destination
architecture), no logic lives here that `core/` doesn't own. This file's only
job is: read input, resolve + call core, print output.

Usage:
    python apps/cli/main.py "your prompt here"                 # routed by MODEL_POLICY
    python apps/cli/main.py "your prompt" --model reasoning-strong   # explicit override
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import load_settings
from core.models.exceptions import ModelError
from core.models.registry import build_default_registry
from core.models.retry import generate_with_retry
from core.models.routing import DEFAULT_TASK_TYPE, route

USAGE = 'Usage: python apps/cli/main.py "<prompt>" [--model <logical-name>]'


def _parse_args(argv: list[str]) -> tuple[str | None, str | None]:
    """Return (prompt, explicit_model).

    explicit_model is None when --model was not given (the caller then routes
    by MODEL_POLICY). prompt is None when it's missing or invalid — which sends
    run() down the usage path. Hand-parsed rather than argparse on purpose:
    argparse runs its own sys.exit on bad input, which would fight run()'s
    clean int return contract that the tests rely on.
    """
    args = argv[1:]
    explicit_model: str | None = None

    if args.count("--model") > 1:
        # Ambiguous — refuse rather than silently pick one and let a stray
        # "--model" token fall through into the prompt slot.
        return None, None

    if "--model" in args:
        i = args.index("--model")
        if i + 1 >= len(args):
            return None, None  # --model with no value -> show usage
        explicit_model = args[i + 1]
        del args[i : i + 2]

    # A surviving "--model" (e.g. the prompt was literally "--model") is not a
    # valid prompt — take the usage path instead of sending it to the model.
    prompt = args[0] if args and args[0].strip() and args[0] != "--model" else None
    return prompt, explicit_model


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
    prompt, explicit_model = _parse_args(argv)
    if prompt is None:
        print(USAGE, file=sys.stderr)
        return 1

    settings = settings_loader()

    if explicit_model is not None:
        logical_model = explicit_model
        selection = f"model={logical_model} (explicit)"
    else:
        logical_model = route(DEFAULT_TASK_TYPE, settings.model_policy)
        selection = f"policy={settings.model_policy} -> {logical_model}"

    try:
        registry = registry_builder(settings)
        result = generate_with_retry(
            registry,
            prompt,
            primary=logical_model,
            fallback=settings.model_fallback or None,
        )
    except ModelError as exc:
        print(f"Error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    print(result.text)
    print(
        f"[{result.provider}/{result.model} — {result.input_tokens} in / "
        f"{result.output_tokens} out tokens — {selection}]",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv))
