"""
Tests for core.models.factory.get_active_provider — proves the switch works
without requiring any real API key for either provider.
"""

from __future__ import annotations

import pytest

from core.config import Settings
from core.models.exceptions import ModelError
from core.models.factory import get_active_provider
from core.models.providers.anthropic_provider import AnthropicProvider
from core.models.providers.openrouter_provider import OpenRouterProvider


def _settings(active_provider: str) -> Settings:
    return Settings(
        anthropic_api_key="fake-anthropic-key",
        model_policy="balanced",
        active_provider=active_provider,
        openrouter_api_key="fake-openrouter-key",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
    )


def test_defaults_to_anthropic_when_configured():
    provider = get_active_provider(_settings("anthropic"))
    assert isinstance(provider, AnthropicProvider)


def test_switches_to_openrouter_when_configured():
    provider = get_active_provider(_settings("openrouter"))
    assert isinstance(provider, OpenRouterProvider)


def test_unknown_provider_raises_clear_error():
    with pytest.raises(ModelError):
        get_active_provider(_settings("something-else"))
