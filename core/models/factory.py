"""
core/models/factory.py

Minimal provider selector — added ahead of schedule to unblock dev/testing
while there are no Anthropic credits. This is NOT the Model Registry
(planned for Session 3 in ROADMAP.md) — it has none of the registry's
capability-matching, cost-awareness, or fallback logic. It does exactly
one thing: read `Settings.active_provider` and hand back the matching
ModelProvider instance.

Session 3 outcome (see DECISIONS.md D007): the Model Registry
(core/models/registry.py) is now the caller-facing resolution layer — the
CLI and every future consumer go through it, not through this function.
This function was NOT deleted; it was retained as the registry's single
provider-construction primitive. `build_default_registry()` calls it, so
ACTIVE_PROVIDER selection and API-key handling still live in exactly one
place. Its role narrowed from "what callers use" to "how the registry
builds the active provider" — no behavior change, no signature change.
"""

from __future__ import annotations

from core.config import Settings
from core.models.base import ModelProvider
from core.models.exceptions import ModelError
from core.models.providers.anthropic_provider import AnthropicProvider
from core.models.providers.openrouter_provider import OpenRouterProvider


def get_active_provider(settings: Settings) -> ModelProvider:
    """Returns the ModelProvider selected by Settings.active_provider.

    Anthropic remains the default — nothing about existing behavior changes
    unless ACTIVE_PROVIDER is explicitly set to "openrouter" in .env.
    """
    if settings.active_provider == "anthropic":
        return AnthropicProvider(api_key=settings.anthropic_api_key)

    if settings.active_provider == "openrouter":
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            default_model=settings.openrouter_model,
        )

    raise ModelError(
        f"Unknown ACTIVE_PROVIDER '{settings.active_provider}' — "
        "expected 'anthropic' or 'openrouter'"
    )
