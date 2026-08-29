"""
Tests for apps/cli/main.py — injects a fake provider/settings, so this
never touches env vars, real credentials, or the network. Mirrors the
injection pattern already used in core/models tests.
"""

from __future__ import annotations

from core.config import Settings
from core.models.base import ModelResponse
from core.models.exceptions import ModelRateLimitError

from apps.cli.main import run


class _FakeProvider:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def generate(self, prompt, **kwargs):
        if self._error is not None:
            raise self._error
        return self._response


def _fake_settings():
    return Settings(
        anthropic_api_key="fake",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="fake",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
    )


def test_run_prints_response_text(capsys):
    fake_response = ModelResponse(
        text="hello back",
        model="claude-sonnet-5",
        provider="anthropic",
        input_tokens=5,
        output_tokens=2,
    )
    provider = _FakeProvider(response=fake_response)

    exit_code = run(
        ["main.py", "say hello"],
        provider_factory=lambda settings: provider,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "hello back"
    assert "anthropic/claude-sonnet-5" in captured.err
    assert "5 in / 2 out" in captured.err


def test_run_with_no_prompt_prints_usage(capsys):
    exit_code = run(["main.py"], provider_factory=lambda settings: _FakeProvider(), settings_loader=_fake_settings)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage:" in captured.err


def test_run_handles_model_error_cleanly(capsys):
    provider = _FakeProvider(error=ModelRateLimitError("slow down"))

    exit_code = run(
        ["main.py", "say hello"],
        provider_factory=lambda settings: provider,
        settings_loader=_fake_settings,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ModelRateLimitError" in captured.err
    assert "slow down" in captured.err
    # no raw traceback leaked to the user
    assert "Traceback" not in captured.err
