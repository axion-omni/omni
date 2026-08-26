"""
core/models/providers/anthropic_provider.py

Stage 1 brick: first real provider implementation.

This is the ONLY file in the system that imports the `anthropic` package.
If Anthropic changes their SDK, this is the only file that changes.
"""

from __future__ import annotations

from typing import Optional

from core.models.base import ModelCapabilities, ModelProvider, ModelResponse
from core.models.exceptions import (
    ModelAuthError,
    ModelError,
    ModelInvalidRequestError,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)

DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider(ModelProvider):
    name = "anthropic"

    def __init__(self, api_key: str, client_factory=None):
        """
        client_factory lets tests inject a fake client instead of the real
        anthropic.Anthropic(...) — this is what makes Stage 1 testable
        without a live API key or network call.
        """
        if not api_key:
            raise ModelAuthError("ANTHROPIC_API_KEY is missing")

        if client_factory is not None:
            self._client = client_factory(api_key=api_key)
        else:
            import anthropic  # imported lazily so tests never need the package installed with network reachability

            self._client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        model: Optional[str] = None,
    ) -> ModelResponse:
        model = model or DEFAULT_MODEL
        try:
            kwargs = dict(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            if system:
                kwargs["system"] = system

            resp = self._client.messages.create(**kwargs)

        except Exception as exc:  # translate SDK-specific errors → our exceptions
            self._translate_and_raise(exc)

        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )

        return ModelResponse(
            text=text,
            model=model,
            provider=self.name,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,
            raw=resp,
        )

    def capabilities(self, model: Optional[str] = None) -> ModelCapabilities:
        model = model or DEFAULT_MODEL
        # Conservative defaults for the Sonnet-class model. Refined per-model
        # once the capability registry (Stage 2) exists.
        return ModelCapabilities(
            supports_tool_calling=True,
            supports_structured_output=True,
            supports_vision=True,
            max_context_tokens=200_000,
            cost_per_million_input=3.0,
            cost_per_million_output=15.0,
        )

    @staticmethod
    def _translate_and_raise(exc: Exception) -> None:
        name = type(exc).__name__
        msg = str(exc)
        if "AuthenticationError" in name:
            raise ModelAuthError(msg) from exc
        if "RateLimitError" in name:
            raise ModelRateLimitError(msg) from exc
        if "APITimeoutError" in name or "Timeout" in name:
            raise ModelTimeoutError(msg) from exc
        if "APIConnectionError" in name or "InternalServerError" in name or "OverloadedError" in name:
            raise ModelUnavailableError(msg) from exc
        if "BadRequestError" in name or "InvalidRequestError" in name:
            raise ModelInvalidRequestError(msg) from exc
        raise ModelError(msg) from exc
