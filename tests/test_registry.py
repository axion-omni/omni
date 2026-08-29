"""
Tests for core.models.registry — proves logical-name resolution, provider-
sourced capabilities, the per-call cost helper, and the default registry's
provider selection, all without a real API key or any network call
(verification level 2). Mirrors the fake-injection discipline of the other
core/models tests.
"""

from __future__ import annotations

import pytest

from core.config import Settings
from core.models.base import ModelCapabilities, ModelProvider, ModelResponse
from core.models.exceptions import ModelError, ModelNotRegisteredError
from core.models.providers.anthropic_provider import AnthropicProvider
from core.models.providers.openrouter_provider import OpenRouterProvider

from core.models.registry import (
    DEFAULT_LOGICAL_MODEL,
    LOGICAL_MODEL_NAMES,
    ModelRegistry,
    build_default_registry,
    estimated_cost,
)


class _FakeProvider(ModelProvider):
    """Minimal ModelProvider stand-in — records the model id it was asked
    about so tests can prove the registry threads model_id through."""

    name = "fake"

    def __init__(self, capabilities: ModelCapabilities | None = None):
        self._capabilities = capabilities or ModelCapabilities(max_context_tokens=1234)
        self.capabilities_called_with: str | None = None

    def generate(self, prompt, **kwargs):  # pragma: no cover - not exercised here
        raise NotImplementedError

    def capabilities(self, model=None) -> ModelCapabilities:
        self.capabilities_called_with = model
        return self._capabilities


def _settings(active_provider: str = "anthropic") -> Settings:
    return Settings(
        anthropic_api_key="fake-anthropic-key",
        model_policy="balanced",
        active_provider=active_provider,
        openrouter_api_key="fake-openrouter-key",
        openrouter_model="meta-llama/llama-3.3-70b-instruct:free",
    )


# --- resolution ------------------------------------------------------------

def test_register_then_resolve_returns_provider_and_model_id():
    provider = _FakeProvider()
    registry = ModelRegistry()
    registry.register("reasoning-strong", provider, "some-model-id")

    resolved_provider, model_id = registry.resolve("reasoning-strong")

    assert resolved_provider is provider
    assert model_id == "some-model-id"


def test_resolve_unknown_name_raises_model_not_registered_not_keyerror():
    registry = ModelRegistry()

    # It must be a ModelError subclass (so callers catch one type)...
    assert issubclass(ModelNotRegisteredError, ModelError)
    with pytest.raises(ModelNotRegisteredError) as excinfo:
        registry.resolve("does-not-exist")

    # ...and it must NOT be a bare KeyError leaking upward.
    assert not isinstance(excinfo.value, KeyError)
    assert "does-not-exist" in str(excinfo.value)


def test_unknown_name_is_catchable_as_model_error():
    registry = ModelRegistry()
    with pytest.raises(ModelError):
        registry.resolve("nope")


def test_contains_and_list_models_sorted():
    provider = _FakeProvider()
    registry = ModelRegistry()
    registry.register("coding", provider, "m")
    registry.register("cheap-fast", provider, "m")

    assert "coding" in registry
    assert "absent" not in registry
    assert registry.list_models() == ["cheap-fast", "coding"]  # sorted


# --- capabilities are sourced from the provider ----------------------------

def test_capabilities_come_from_the_provider_for_the_resolved_model():
    caps = ModelCapabilities(max_context_tokens=4242, cost_per_million_input=1.5)
    provider = _FakeProvider(capabilities=caps)
    registry = ModelRegistry()
    registry.register("coding", provider, "concrete-model-7")

    returned = registry.capabilities("coding")

    assert returned is caps
    # proves the registry resolved model_id and passed it to the provider
    assert provider.capabilities_called_with == "concrete-model-7"


# --- per-call cost helper --------------------------------------------------

def test_estimated_cost_math():
    caps = ModelCapabilities(cost_per_million_input=3.0, cost_per_million_output=15.0)
    response = ModelResponse(
        text="", model="m", provider="p", input_tokens=1000, output_tokens=500
    )
    # 1000/1e6*3 + 500/1e6*15 = 0.003 + 0.0075
    assert estimated_cost(caps, response) == pytest.approx(0.0105)


def test_estimated_cost_is_zero_for_a_free_model():
    caps = ModelCapabilities(cost_per_million_input=0.0, cost_per_million_output=0.0)
    response = ModelResponse(
        text="", model="m", provider="p", input_tokens=9999, output_tokens=9999
    )
    assert estimated_cost(caps, response) == 0.0


# --- default registry built from Settings (reuses the factory) -------------

def test_build_default_registry_defaults_to_anthropic():
    registry = build_default_registry(_settings("anthropic"))
    provider, model_id = registry.resolve(DEFAULT_LOGICAL_MODEL)

    assert isinstance(provider, AnthropicProvider)
    assert model_id == "claude-sonnet-5"


def test_build_default_registry_switches_to_openrouter():
    settings = _settings("openrouter")
    registry = build_default_registry(settings)
    provider, model_id = registry.resolve("cheap-fast")

    assert isinstance(provider, OpenRouterProvider)
    assert model_id == settings.openrouter_model


def test_build_default_registry_registers_every_logical_name():
    registry = build_default_registry(_settings("anthropic"))
    assert set(registry.list_models()) == set(LOGICAL_MODEL_NAMES)


def test_build_default_registry_unknown_provider_fails_fast():
    # Preserves the factory's fail-fast behavior through the registry (D004).
    with pytest.raises(ModelError):
        build_default_registry(_settings("something-else"))
