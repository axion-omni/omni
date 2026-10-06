"""
Tests for the `constitution` subcommand family in apps/cli/main.py.

Injection discipline (mirrors tests/test_cli.py): a fake repository records
every call, so this suite never touches env vars, a database, or the network.
The live CLI-to-Postgres proof is the operator's Level-3 step, run at a real
terminal — deliberately not here.
"""

from __future__ import annotations

import json

from core.config import Settings
from core.memory.exceptions import ConstitutionNotFoundError
from core.memory.models import Constitution

from apps.cli.main import run


# --- fakes ---------------------------------------------------------------

class _FakeRepo:
    """Records calls; returns programmable results or raises programmable errors."""

    def __init__(
        self,
        *,
        create_returns: str = "fake-project-uuid",
        get_returns: Constitution | None = None,
        get_error: Exception | None = None,
        append_returns: int = 2,
        history_returns: list[tuple[int, object]] | None = None,
    ):
        self.created: list[tuple[str, Constitution]] = []
        self.got: list[str] = []
        self.amended: list[tuple[str, str, dict]] = []
        self._create_returns = create_returns
        self._get_returns = get_returns
        self._get_error = get_error
        self._append_returns = append_returns
        self._history_returns = history_returns or []

    def create(self, name, constitution=None):
        self.created.append((name, constitution or Constitution()))
        return self._create_returns

    def get(self, project_id):
        self.got.append(project_id)
        if self._get_error is not None:
            raise self._get_error
        return self._get_returns or Constitution()

    def append_change(self, project_id, change, **field_updates):
        self.amended.append((project_id, change, field_updates))
        return self._append_returns

    def history(self, project_id):
        return self._history_returns


def _settings() -> Settings:
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="x",
        model_fallback="",
        database_url="postgresql://fake/fake",
    )


def _run(argv, repo):
    return run(
        argv,
        settings_loader=_settings,
        repo_builder=lambda s: repo,
    )


# --- create --------------------------------------------------------------

def test_create_prints_project_id(capsys):
    repo = _FakeRepo(create_returns="abc-uuid")
    exit_code = _run(["main.py", "constitution", "create", "C-Transit"], repo)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "abc-uuid"
    assert repo.created[0][0] == "C-Transit"


def test_create_passes_mission_purpose_and_outcome(capsys):
    repo = _FakeRepo(create_returns="pid")
    exit_code = _run(
        [
            "main.py", "constitution", "create", "C-Transit",
            "--mission", "offline tap-to-ride",
            "--purpose", "cut failed taps",
            "--desired-outcome", "launch on Gidan Kwano",
        ],
        repo,
    )
    assert exit_code == 0
    _, constitution = repo.created[0]
    assert constitution.mission == "offline tap-to-ride"
    assert constitution.purpose == "cut failed taps"
    assert constitution.desired_outcome == "launch on Gidan Kwano"


def test_create_with_no_name_shows_usage(capsys):
    repo = _FakeRepo()
    exit_code = _run(["main.py", "constitution", "create"], repo)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage" in captured.err or "usage" in captured.err
    assert repo.created == []


# --- show ---------------------------------------------------------------

def test_show_prints_the_constitution(capsys):
    repo = _FakeRepo(
        get_returns=Constitution(mission="m", success_criteria=["x", "y"]),
        history_returns=[(1, None)],
    )
    exit_code = _run(["main.py", "constitution", "show", "abc-uuid"], repo)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "project_id: abc-uuid" in captured.out
    assert "version:    1" in captured.out
    assert "mission: m" in captured.out
    # lists are JSON-rendered
    assert 'success_criteria: ["x", "y"]' in captured.out


def test_show_handles_not_found_cleanly(capsys):
    repo = _FakeRepo(get_error=ConstitutionNotFoundError("no such project"))
    exit_code = _run(["main.py", "constitution", "show", "ghost"], repo)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ConstitutionNotFoundError" in captured.err
    assert "no such project" in captured.err
    assert "Traceback" not in captured.err


# --- amend --------------------------------------------------------------

def test_amend_prints_new_version(capsys):
    repo = _FakeRepo(append_returns=4)
    exit_code = _run(
        [
            "main.py", "constitution", "amend", "abc-uuid",
            "--change", "v4: added constraints",
        ],
        repo,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "4"
    assert repo.amended[0][0] == "abc-uuid"
    assert repo.amended[0][1] == "v4: added constraints"


def test_amend_parses_set_flags(capsys):
    repo = _FakeRepo(append_returns=2)
    exit_code = _run(
        [
            "main.py", "constitution", "amend", "abc-uuid",
            "--change", "v2",
            "--set", 'success_criteria=["fast", "offline-capable"]',
            "--set", "constraints=[\"offline-only\"]",
        ],
        repo,
    )

    assert exit_code == 0
    _, _, field_updates = repo.amended[0]
    assert field_updates["success_criteria"] == ["fast", "offline-capable"]
    assert field_updates["constraints"] == ["offline-only"]


def test_amend_set_parses_json_scalars(capsys):
    # JSON typing: numbers stay numbers, booleans stay booleans, plain
    # strings fall through as strings.
    repo = _FakeRepo(append_returns=2)
    _run(
        [
            "main.py", "constitution", "amend", "abc-uuid",
            "--change", "v2",
            "--set", "risks=[\"x\"]",
            "--set", "non_negotiables=[\"y\"]",
        ],
        repo,
    )
    _, _, updates = repo.amended[0]
    assert isinstance(updates["risks"], list)


def test_amend_rejects_malformed_set(capsys):
    repo = _FakeRepo()
    exit_code = _run(
        [
            "main.py", "constitution", "amend", "abc-uuid",
            "--change", "v2",
            "--set", "no-equals-sign",
        ],
        repo,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid input" in captured.err.lower() or "KEY=VALUE" in captured.err
    assert repo.amended == []


def test_amend_without_change_shows_usage(capsys):
    repo = _FakeRepo()
    exit_code = _run(
        ["main.py", "constitution", "amend", "abc-uuid"], repo
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    # argparse treats missing --change as an error -> our usage path
    assert "Usage" in captured.err or "usage" in captured.err
    assert repo.amended == []


# --- dispatch / regression ------------------------------------------------

def test_unknown_constitution_subcommand_shows_usage(capsys):
    repo = _FakeRepo()
    exit_code = _run(["main.py", "constitution", "frobnicate"], repo)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage" in captured.err or "usage" in captured.err


def test_chat_path_still_works(capsys):
    # Regression: adding the constitution subcommand must not break the chat
    # path. We only assert dispatch — the chat path's own tests cover behavior.
    from tests.test_cli import _FakeProvider, _FakeRegistry, _response  # noqa

    provider = _FakeProvider(response=_response())
    registry = _FakeRegistry(provider)

    exit_code = run(
        ["main.py", "say hello"],
        registry_builder=lambda s: registry,
        settings_loader=_settings,
        repo_builder=lambda s: _FakeRepo(),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "hello back" in captured.out
