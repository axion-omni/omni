"""
core/models/base.py

Stage 1 brick: the Model Abstraction Layer.

Nothing else in this system is allowed to import a provider SDK (anthropic,
openai, google-genai, ...) directly. Everything talks to a ModelProvider.
This is the boundary that lets us add a new model by registering it later
(Stage 2 — the registry) instead of rewriting callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ModelResponse:
    """Uniform shape every provider must return, regardless of its own API shape."""

    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    stop_reason: Optional[str] = None
    raw: Any = None  # original SDK response, kept for debugging only — never
    # depended on by calling code, or the abstraction is broken.

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ModelCapabilities:
    """What a given model can do — used by the router (Stage 2) to pick a model."""

    supports_tool_calling: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    max_context_tokens: int = 0
    # rough $ per million tokens, input/output — used for cost-aware routing later
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0


class ModelProvider(ABC):
    """
    The contract every provider (Anthropic, OpenAI, local, ...) must satisfy.

    Deliberately small at this stage: one method. Tool calling, streaming, and
    structured output get added as their own capabilities in later stages
    (Stage 5 — Tool System) rather than bloating this interface now.
    """

    name: str = "unnamed-provider"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        model: Optional[str] = None,
    ) -> ModelResponse:
        """Send a single prompt, get back a ModelResponse. Must raise a
        core.models.exceptions.ModelError subclass on failure — never let a
        raw SDK exception escape this method."""
        raise NotImplementedError

    @abstractmethod
    def capabilities(self, model: Optional[str] = None) -> ModelCapabilities:
        """Describe what this provider/model can do, for routing decisions."""
        raise NotImplementedError
