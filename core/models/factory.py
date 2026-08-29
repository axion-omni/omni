"""
core/models/factory.py

Minimal provider selector — added ahead of schedule to unblock dev/testing
while there are no Anthropic credits. This is NOT the Model Registry
(planned for Session 3 in ROADMAP.md) — it has none of the registry's
capability-matching, cost-awareness, or fallback logic. It does exactly
one thing: read `Settings.active_provider` and hand back the matching
ModelProvider instance.

Session 3 will absorb this function's job into the real registry. When
that happens, this file either gets deleted or becomes a thin wrapper
around the registry — logged as a forward-looking note, not a decision
that needs to be re-litigated later (see DECISIONS.md D004).
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
