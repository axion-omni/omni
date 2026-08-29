"""
Tests for OpenRouterProvider — same discipline as test_anthropic_provider.py:
a fake HTTP session stands in for `requests`, so this runs with no real
network call and no real API key (verification level 2). Run
scripts/smoke_test_openrouter.py for the real, network-hitting level-3 check.
"""

from __future__ import annotations

import pytest

from core.models.base import ModelResponse
from core.models.exceptions import ModelAuthError, ModelRateLimitError
from core.models.providers.openrouter_provider import OpenRouterProvider


class _FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or str(json_data)

    def json(self):
        return self._json_data


class _FakeSession:
    def __init__(self, response):
        self._response = response
        self.last_call = None

    def post(self, url, headers=None, json=None, timeout=None):
        self.last_call = {"url": url, "headers": headers, "json": json, "timeout": timeout}
        return self._response


def _success_response(text="hello from llama", model="meta-llama/llama-3.3-70b-instruct:free"):
    return _FakeResponse(
        200,
        json_data={
            "model": model,
            "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 5},
        },
    )


def test_generate_returns_uniform_model_response():
    session = _FakeSession(_success_response())
    provider = OpenRouterProvider(api_key="fake-key", session=session)

    result = provider.generate("say hello")

    assert isinstance(result, ModelResponse)
    assert result.text == "hello from llama"
    assert result.provider == "openrouter"
    assert result.input_tokens == 12
    assert result.output_tokens == 5
    assert result.total_tokens == 17
    assert result.stop_reason == "stop"


def test_default_model_is_free_tier_llama():
    session = _FakeSession(_success_response())
    provider = OpenRouterProvider(api_key="fake-key", session=session)

    provider.generate("say hello")

    assert session.last_call["json"]["model"] == "meta-llama/llama-3.3-70b-instruct:free"


def test_missing_api_key_raises_model_auth_error():
    with pytest.raises(ModelAuthError):
        OpenRouterProvider(api_key="", session=_FakeSession(_success_response()))


def test_401_response_raises_model_auth_error():
    session = _FakeSession(_FakeResponse(401, text="invalid key"))
    provider = OpenRouterProvider(api_key="fake-key", session=session)

    with pytest.raises(ModelAuthError):
        provider.generate("say hello")


def test_429_response_raises_model_rate_limit_error():
    session = _FakeSession(_FakeResponse(429, text="rate limited"))
    provider = OpenRouterProvider(api_key="fake-key", session=session)

    with pytest.raises(ModelRateLimitError):
        provider.generate("say hello")


def test_capabilities_reports_free_pricing():
    provider = OpenRouterProvider(api_key="fake-key", session=_FakeSession(_success_response()))
    caps = provider.capabilities()
    assert caps.cost_per_million_input == 0.0
    assert caps.cost_per_million_output == 0.0
    assert caps.max_context_tokens == 131_072


def test_custom_model_override_is_used():
    session = _FakeSession(_success_response(model="deepseek/deepseek-r1:free"))
    provider = OpenRouterProvider(
        api_key="fake-key", default_model="deepseek/deepseek-r1:free", session=session
    )

    provider.generate("say hello")

    assert session.last_call["json"]["model"] == "deepseek/deepseek-r1:free"
