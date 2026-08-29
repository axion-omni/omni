"""
core/models/registry.py

Session 3 brick (Stage 2 — Model Abstraction & Routing): the Model Registry.

Callers ask for a *logical* model name ("reasoning-strong", "cheap-fast",
"coding") and get back a ready-to-use (provider, model_id) pair — they never
write a raw provider name or a concrete model string. This is the layer that
makes the standing lock-in rule real: adding a model later is one new provider
file plus one registry entry, with zero caller-side changes (Master
Construction Specification, Part V and Part XXII).

Relationship to core/models/factory.py (see DECISIONS.md D007):
    The factory still owns the single decision of *which provider instance* to
    construct from Settings (ACTIVE_PROVIDER + keys). The registry sits on top
    of it and maps logical names onto (that provider, a concrete model_id).
    The factory is now the registry's construction primitive, not a
    caller-facing entry point — callers go through the registry from here on.

Capabilities are not duplicated here. `capabilities(logical_name)` resolves the
pair and asks the provider itself (`ModelProvider.capabilities(model_id)`),
exactly as Part V specifies ("seeded from ModelProvider.capabilities()"). The
registry is where cost/capability data is *queried from* (Personal AI OS
architecture, Section 9), not a second source of truth for it.

Scope, deliberately small (Part VII, Session 3): we have one verified model per
provider today, so every logical name resolves to the active provider's real
model. The task-type + MODEL_POLICY routing table that makes these names differ
is Session 4 (core/models/routing.py); retry/fallback is Session 5.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.config import Settings
from core.models.base import ModelCapabilities, ModelProvider, ModelResponse
from core.models.exceptions import ModelNotRegisteredError
from core.models.factory import get_active_provider
from core.models.providers.anthropic_provider import (
    DEFAULT_MODEL as ANTHROPIC_DEFAULT_MODEL,
)

# Logical names a caller may ask for. Kept intentionally short at Session 3;
# Session 4's routing layer decides which of these a given (task type, policy)
# maps to once more than one real model is registered behind them.
DEFAULT_LOGICAL_MODEL = "reasoning-strong"
LOGICAL_MODEL_NAMES = ("reasoning-strong", "coding", "cheap-fast")


@dataclass(frozen=True)
class RegisteredModel:
    """One registry entry: a provider instance and the concrete model id to
    pass to that provider's ``generate(..., model=model_id)``."""

    provider: ModelProvider
    model_id: str


class ModelRegistry:
    """Maps logical model names -> (provider, model_id).

    Nothing above this layer should know a concrete model string. Resolving an
    unknown name raises ModelNotRegisteredError (a ModelError) — never a bare
    KeyError leaking upward (Part VII, Session 3 acceptance criterion).
    """

    def __init__(self) -> None:
        self._models: dict[str, RegisteredModel] = {}

    def register(self, logical_name: str, provider: ModelProvider, model_id: str) -> None:
        """Add or replace a logical-name -> (provider, model_id) mapping."""
        self._models[logical_name] = RegisteredModel(provider=provider, model_id=model_id)

    def resolve(self, logical_name: str) -> tuple[ModelProvider, str]:
        """Return the (provider, model_id) pair for a logical name.

        Raises ModelNotRegisteredError (a ModelError subclass) for an unknown
        name, with the list of registered names in the message.
        """
        try:
            entry = self._models[logical_name]
        except KeyError:
            known = ", ".join(sorted(self._models)) or "(none registered)"
            raise ModelNotRegisteredError(
                f"Unknown logical model {logical_name!r}. Known models: {known}."
            ) from None
        return entry.provider, entry.model_id

    def capabilities(self, logical_name: str) -> ModelCapabilities:
        """Capability/cost metadata for a logical name, sourced from the
        provider (Part V: seeded from ModelProvider.capabilities())."""
        provider, model_id = self.resolve(logical_name)
        return provider.capabilities(model_id)

    def list_models(self) -> list[str]:
        """Registered logical names, sorted — for CLI help and observability."""
        return sorted(self._models)

    def __contains__(self, logical_name: object) -> bool:
        return logical_name in self._models


def estimated_cost(capabilities: ModelCapabilities, response: ModelResponse) -> float:
    """USD cost of a single response: token counts x per-million rates.

    Pure and side-effect free. This is the per-call building block the
    Orchestrator's cost-to-date reporting is built on (Personal AI OS
    architecture, Sections 9 and 13; Master Construction Spec, Part XIX). The
    running per-project total lives in the event log later (Stage 16), not
    here — this function is only the arithmetic for one call.
    """
    return (
        response.input_tokens / 1_000_000 * capabilities.cost_per_million_input
        + response.output_tokens / 1_000_000 * capabilities.cost_per_million_output
    )


def build_default_registry(settings: Settings) -> ModelRegistry:
    """Construct the default registry from Settings.

    Reuses core.models.factory.get_active_provider() so provider selection and
    API-key handling live in exactly one place (D004/D005). The active provider
    is registered under every logical name; the concrete model_id is that
    provider's default — Anthropic's DEFAULT_MODEL, or OPENROUTER_MODEL on the
    OpenRouter path, so D004's no-Anthropic-credit dev route stays intact.

    Raises ModelError (via the factory) if ACTIVE_PROVIDER is unknown — the
    same fail-fast behavior the factory already had.
    """
    provider = get_active_provider(settings)
    model_id = _default_model_id_for(settings)

    registry = ModelRegistry()
    for logical_name in LOGICAL_MODEL_NAMES:
        registry.register(logical_name, provider, model_id)
    return registry


def _default_model_id_for(settings: Settings) -> str:
    """The concrete model id the active provider should be called with.

    Only reached for providers get_active_provider() already accepted, so it
    never has to guard against an unknown provider string.
    """
    if settings.active_provider == "openrouter":
        return settings.openrouter_model
    return ANTHROPIC_DEFAULT_MODEL
