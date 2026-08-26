"""
Session 1 acceptance test.

These tests prove the abstraction contract holds WITHOUT needing a live
Anthropic API key — that's intentional. A fake client stands in for the SDK.
Once you add a real ANTHROPIC_API_KEY to .env, run scripts/smoke_test.py for
a live, network-hitting sanity check. Keep both: unit tests for CI/every
commit, smoke test for "does my key/network actually work today."
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.models.base import ModelResponse
from core.models.exceptions import ModelAuthError, ModelRateLimitError
from core.models.providers.anthropic_provider import AnthropicProvider


class _FakeContentBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeMessages:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def create(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response=None, error=None, **_kwargs):
        self.messages = _FakeMessages(response=response, error=error)


def _make_fake_response(text="hello from claude", input_tokens=10, output_tokens=4):
    return SimpleNamespace(
        content=[_FakeContentBlock(text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        stop_reason="end_turn",
    )


def test_generate_returns_uniform_model_response():
    fake_resp = _make_fake_response()
    provider = AnthropicProvider(
        api_key="fake-key",
        client_factory=lambda api_key: _FakeAnthropicClient(response=fake_resp),
    )

    result = provider.generate("say hello")

    assert isinstance(result, ModelResponse)
    assert result.text == "hello from claude"
    assert result.provider == "anthropic"
    assert result.input_tokens == 10
    assert result.output_tokens == 4
    assert result.total_tokens == 14
    assert result.stop_reason == "end_turn"


def test_missing_api_key_raises_model_auth_error():
    with pytest.raises(ModelAuthError):
        AnthropicProvider(api_key="", client_factory=lambda api_key: _FakeAnthropicClient())


def test_sdk_rate_limit_error_is_translated():
    class FakeRateLimitError(Exception):
        pass

    FakeRateLimitError.__name__ = "RateLimitError"

    provider = AnthropicProvider(
        api_key="fake-key",
        client_factory=lambda api_key: _FakeAnthropicClient(error=FakeRateLimitError("slow down")),
    )

    with pytest.raises(ModelRateLimitError):
        provider.generate("say hello")


def test_capabilities_reports_context_window():
    provider = AnthropicProvider(
        api_key="fake-key",
        client_factory=lambda api_key: _FakeAnthropicClient(response=_make_fake_response()),
    )
    caps = provider.capabilities()
    assert caps.max_context_tokens == 200_000
    assert caps.supports_tool_calling is True
