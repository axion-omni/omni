"""
apps/cli/main.py

Session 2 brick, extended in Sessions 3–4: the terminal interface resolves a
*logical* model name through the Model Registry, choosing that name by
MODEL_POLICY (Session 4 routing) unless an explicit --model overrides it.

Session 9 adds a `constitution` subcommand family backed by the Constitution
repository (Session 8). This is the CLI's first path to persistent state:
create a Constitution in one process, read it back in another. That is
Milestone C's definition of done.

Deliberately thin — this is an interface, not intelligence. Per
SYSTEM_ARCHITECTURE.md's standing rule (and D003 / Section 3 of the destination
architecture), no logic lives here that `core/` doesn't own. This file's only
job is: read input, call core, print output. Handlers here do NOT contain
validation, business rules, or storage logic — they parse argv, call one
core method, and format the result.

Usage:
    python apps/cli/main.py "<prompt>" [--model <logical-name>]     # chat
    python apps/cli/main.py constitution create <name> [--mission "..."] [--purpose "..."] ...
    python apps/cli/main.py constitution show <project_id>
    python apps/cli/main.py constitution amend <project_id> --change "<desc>" [--set k=v]...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.config import Settings, load_settings
from core.memory.constitution import ConstitutionRepository
from core.memory.exceptions import MemoryError
from core.memory.models import Constitution
from core.models.exceptions import ModelError
from core.models.registry import build_default_registry
from core.models.retry import generate_with_retry
from core.models.routing import DEFAULT_TASK_TYPE, route

CHAT_USAGE = 'Usage: python apps/cli/main.py "<prompt>" [--model <logical-name>]'
CONSTITUTION_USAGE = (
    "Usage:\n"
    "  constitution create <name> [--mission TEXT] [--purpose TEXT]\n"
    "                             [--desired-outcome TEXT]\n"
    "  constitution show <project_id>\n"
    "  constitution amend <project_id> --change TEXT [--set KEY=VALUE]..."
)


# =========================================================================
# Chat path (Sessions 2–5) — unchanged behavior, unchanged parser
# =========================================================================

def _parse_chat_args(argv: list[str]) -> tuple[str | None, str | None]:
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
        return None, None

    if "--model" in args:
        i = args.index("--model")
        if i + 1 >= len(args):
            return None, None
        explicit_model = args[i + 1]
        del args[i : i + 2]

    prompt = args[0] if args and args[0].strip() and args[0] != "--model" else None
    return prompt, explicit_model


def _run_chat(
    argv: list[str],
    registry_builder: Callable[[Settings], Any],
    settings_loader: Callable[[], Settings],
) -> int:
    prompt, explicit_model = _parse_chat_args(argv)
    if prompt is None:
        print(CHAT_USAGE, file=sys.stderr)
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


# =========================================================================
# Constitution subcommands (Session 9) — thin wrappers over the repository
# =========================================================================

def _build_constitution_parser() -> argparse.ArgumentParser:
    """The `constitution` subcommand tree.

    argparse is used here (not the chat path's hand-parse) because these
    subcommands have real flags and argparse's errors are useful to a human
    at a terminal. We do NOT use argparse in the chat path because there the
    hand-parse keeps a clean int-return contract that the tests depend on.
    """
    parser = argparse.ArgumentParser(
        prog="constitution", add_help=False,
        description="Manage Project Constitutions (persistent, append-only, versioned).",
    )
    sub = parser.add_subparsers(dest="subcommand")

    p_create = sub.add_parser("create", add_help=False)
    p_create.add_argument("name")
    p_create.add_argument("--mission", default="")
    p_create.add_argument("--purpose", default="")
    p_create.add_argument("--desired-outcome", dest="desired_outcome", default="")

    p_show = sub.add_parser("show", add_help=False)
    p_show.add_argument("project_id")

    p_amend = sub.add_parser("amend", add_help=False)
    p_amend.add_argument("project_id")
    p_amend.add_argument("--change", required=True)
    p_amend.add_argument(
        "--set", dest="sets", action="append", default=[],
        metavar="KEY=VALUE",
        help="Set a Constitution field. Repeatable. VALUE is parsed as JSON "
             "when valid (so lists/numbers/booleans work), otherwise a string.",
    )

    return parser


def _parse_set_flag(raw: str) -> tuple[str, Any]:
    """Parse one '--set KEY=VALUE' pair. VALUE is JSON when valid, else str.

    Rigid: a malformed 'KEY=VALUE' (no '=') raises ValueError, which the
    handler surfaces as a clean error — never a silent no-op.
    """
    if "=" not in raw:
        raise ValueError(
            f"--set expects KEY=VALUE, got {raw!r}. Example: "
            f"--set constraints='[\"offline-only\"]'"
        )
    key, _, value = raw.partition("=")
    key = key.strip()
    if not key:
        raise ValueError(f"--set expects a non-empty KEY, got {raw!r}.")
    try:
        parsed_value: Any = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
    return key, parsed_value


def _format_constitution(project_id: str, constitution: Constitution, version: int) -> str:
    """Human-readable, one field per line, lists rendered as compact JSON."""
    lines = [
        f"project_id: {project_id}",
        f"version:    {version}",
        "",
    ]
    for field_name, value in constitution.model_dump().items():
        if isinstance(value, list):
            rendered = json.dumps(value)
        else:
            rendered = value
        lines.append(f"{field_name}: {rendered}")
    return "\n".join(lines)


def _run_constitution(
    argv_after_constitution: list[str],
    settings_loader: Callable[[], Settings],
    repo_builder: Callable[[Settings], ConstitutionRepository],
) -> int:
    parser = _build_constitution_parser()
    try:
        args = parser.parse_args(argv_after_constitution)
    except SystemExit:
        # argparse exits on parse errors; we return an int instead.
        print(CONSTITUTION_USAGE, file=sys.stderr)
        return 1

    if args.subcommand is None:
        print(CONSTITUTION_USAGE, file=sys.stderr)
        return 1

    settings = settings_loader()

    try:
        repo = repo_builder(settings)

        if args.subcommand == "create":
            constitution = Constitution(
                mission=args.mission,
                purpose=args.purpose,
                desired_outcome=args.desired_outcome,
            )
            project_id = repo.create(args.name, constitution)
            print(project_id)
            return 0

        if args.subcommand == "show":
            constitution = repo.get(args.project_id)
            version = repo.latest_version(args.project_id) \
                if hasattr(repo, "latest_version") else _derive_version(repo, args.project_id)
            print(_format_constitution(args.project_id, constitution, version))
            return 0

        if args.subcommand == "amend":
            field_updates: dict[str, Any] = {}
            for raw in args.sets:
                k, v = _parse_set_flag(raw)
                field_updates[k] = v
            new_version = repo.append_change(
                args.project_id, args.change, **field_updates
            )
            print(new_version)
            return 0

    except MemoryError as exc:
        print(f"Error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error (invalid input): {exc}", file=sys.stderr)
        return 1

    print(CONSTITUTION_USAGE, file=sys.stderr)
    return 1


def _derive_version(repo: ConstitutionRepository, project_id: str) -> int:
    """Fallback if the repository has no latest_version() — derive from history.

    S8 built history() but not latest_version(); rather than change S8's
    contract in S9, we derive. If S8 gains latest_version later, the hasattr
    branch above uses it directly.
    """
    rows = repo.history(project_id)
    return rows[-1][0] if rows else 1


# =========================================================================
# Entry point
# =========================================================================

def run(
    argv: list[str],
    registry_builder: Callable[[Settings], Any] = build_default_registry,
    settings_loader: Callable[[], Settings] = load_settings,
    repo_builder: Optional[Callable[[Settings], ConstitutionRepository]] = None,
) -> int:
    """
    registry_builder / settings_loader / repo_builder are injectable so tests
    can run this against fakes without touching env vars, the network, or a
    database — the same injection pattern used throughout core/.

    Dispatch: argv[1] == "constitution" -> constitution handler; anything else
    -> chat handler. This keeps every existing chat test green unchanged.
    """
    if len(argv) >= 2 and argv[1] == "constitution":
        settings_loader_local = settings_loader
        repo_builder_local = repo_builder or (lambda s: ConstitutionRepository(s))
        return _run_constitution(
            argv[2:], settings_loader_local, repo_builder_local
        )

    return _run_chat(argv, registry_builder, settings_loader)


if __name__ == "__main__":
    sys.exit(run(sys.argv))
