"""
Tests for apps/cli/main.py — injects a fake registry/settings, so this never
touches env vars, real credentials, or the network. Mirrors the injection
pattern already used in core/models tests.
"""

from __future__ import annotations

from core.config import Settings
from core.models.base import ModelResponse
from core.models.exceptions import ModelNotRegisteredError, ModelRateLimitError

from apps.cli.main import run


class _FakeProvider:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.generate_called_with: dict | None = None

    def generate(self, prompt, **kwargs):
        self.generate_called_with = {"prompt": prompt, **kwargs}
        if self._error is not None:
            raise self._error
        return self._response


class _FakeRegistry:
    """Stands in for ModelRegistry: records which logical name was resolved."""

    def __init__(self, provider, model_id="claude-sonnet-5", error=None):
        self._provider = provider
        self._model_id = model_id
        self._error = error
        self.resolved: list[str] = []

    def resolve(self, logical_name):
        self.resolved.append(logical_name)
        if self._error is not None:
            raise self._error
        return self._provider, self._model_id


def _fake_settings():
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
    )


def _response(text="hello back", model="claude-sonnet-5"):
    return ModelResponse(
        text=text, model=model, provider="anthropic", input_tokens=5, output_tokens=2
    )


def test_run_prints_response_text(capsys):
    provider = _FakeProvider(response=_response())
    registry = _FakeRegistry(provider)

    exit_code = run(
        ["main.py", "say hello"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "hello back"
    assert "anthropic/claude-sonnet-5" in captured.err
    assert "5 in / 2 out" in captured.err


def test_run_defaults_to_the_default_logical_model(capsys):
    provider = _FakeProvider(response=_response())
    registry = _FakeRegistry(provider)

    run(
        ["main.py", "say hello"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    # no --model given -> the registry's default logical name was resolved
    assert registry.resolved == ["reasoning-strong"]


def test_run_passes_model_flag_to_registry(capsys):
    provider = _FakeProvider(response=_response())
    registry = _FakeRegistry(provider)

    exit_code = run(
        ["main.py", "say hello", "--model", "cheap-fast"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    assert exit_code == 0
    assert registry.resolved == ["cheap-fast"]
    # and the resolved model_id was threaded into generate()
    assert provider.generate_called_with["model"] == "claude-sonnet-5"


def test_run_with_no_prompt_prints_usage(capsys):
    registry = _FakeRegistry(_FakeProvider())
    exit_code = run(
        ["main.py"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage:" in captured.err


def test_run_handles_model_error_cleanly(capsys):
    provider = _FakeProvider(error=ModelRateLimitError("slow down"))
    registry = _FakeRegistry(provider)

    exit_code = run(
        ["main.py", "say hello"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ModelRateLimitError" in captured.err
    assert "slow down" in captured.err
    # no raw traceback leaked to the user
    assert "Traceback" not in captured.err


def test_run_handles_unknown_model_name_cleanly(capsys):
    registry = _FakeRegistry(
        _FakeProvider(), error=ModelNotRegisteredError("Unknown logical model 'bogus'.")
    )

    exit_code = run(
        ["main.py", "say hello", "--model", "bogus"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ModelNotRegisteredError" in captured.err
    assert "Traceback" not in captured.err


def test_run_rejects_duplicate_model_flag(capsys):
    # A repeated --model is ambiguous: show usage, never send "--model" as the
    # prompt or silently pick one flag (regression for the review finding).
    registry = _FakeRegistry(_FakeProvider(response=_response()))
    exit_code = run(
        ["main.py", "--model", "reasoning-strong", "--model", "cheap-fast", "hello"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage:" in captured.err
    assert registry.resolved == []  # nothing was resolved/generated


def test_run_rejects_bare_model_token_as_prompt(capsys):
    # `--model` with no value must not be treated as a prompt.
    registry = _FakeRegistry(_FakeProvider(response=_response()))
    exit_code = run(
        ["main.py", "--model"],
        registry_builder=lambda settings: registry,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage:" in captured.err
    assert registry.resolved == []
