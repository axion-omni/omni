"""
core/models/providers/openrouter_provider.py

Added to unblock development/testing while no Anthropic credits are
available. Implements the exact same ModelProvider contract as
AnthropicProvider — nothing outside this file needs to know OpenRouter
exists for the rest of the system to keep working.

OpenRouter exposes an OpenAI-compatible REST API (not a Python SDK we need
to add as a dependency) — a plain `requests` call is enough, which keeps
this dependency-light on purpose.

Free-tier note: OpenRouter's free (":free" suffix) model roster rotates as
providers add/remove capacity. The default below
(meta-llama/llama-3.3-70b-instruct:free) was, as of Aug 2026, the
longest-running and most stable free general-purpose model on the platform.
If it stops working, check https://openrouter.ai/models (filter: Free) and
override via the OPENROUTER_MODEL env var — no code change needed.
"""

from __future__ import annotations

from typing import Optional

import requests

from core.models.base import ModelCapabilities, ModelProvider, ModelResponse
from core.models.exceptions import (
    ModelAuthError,
    ModelError,
    ModelInvalidRequestError,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_FREE_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


class OpenRouterProvider(ModelProvider):
    name = "openrouter"

    def __init__(self, api_key: str, default_model: Optional[str] = None, session=None):
        """
        `session` lets tests inject a fake HTTP session instead of making a
        real network call — same pattern as AnthropicProvider's
        client_factory, for the same reason (testable without a real key).
        """
        if not api_key:
            raise ModelAuthError("OPENROUTER_API_KEY is missing")

        self._api_key = api_key
        self._default_model = default_model or DEFAULT_FREE_MODEL
        self._session = session or requests

    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        model: Optional[str] = None,
    ) -> ModelResponse:
        model = model or self._default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = self._session.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    # Optional but recommended by OpenRouter for attribution;
                    # harmless if ignored by the endpoint.
                    "X-Title": "ai-project-execution-engine",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=60,
            )
        except requests.exceptions.Timeout as exc:
            raise ModelTimeoutError(str(exc)) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ModelUnavailableError(str(exc)) from exc
        except requests.exceptions.RequestException as exc:
            raise ModelError(str(exc)) from exc

        self._raise_for_status(resp)

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return ModelResponse(
            text=choice["message"]["content"],
            model=data.get("model", model),
            provider=self.name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            stop_reason=choice.get("finish_reason"),
            raw=data,
        )

    def capabilities(self, model: Optional[str] = None) -> ModelCapabilities:
        # Conservative defaults for the free-tier Llama 3.3 70B model.
        # Refined per-model once the capability registry (Session 3) exists.
        return ModelCapabilities(
            supports_tool_calling=False,
            supports_structured_output=False,
            supports_vision=False,
            max_context_tokens=131_072,
            cost_per_million_input=0.0,
            cost_per_million_output=0.0,
        )

    @staticmethod
    def _raise_for_status(resp) -> None:
        if resp.status_code == 200:
            return
        if resp.status_code == 401:
            raise ModelAuthError(f"OpenRouter auth failed: {resp.text}")
        if resp.status_code == 429:
            raise ModelRateLimitError(f"OpenRouter rate limit: {resp.text}")
        if resp.status_code in (408,):
            raise ModelTimeoutError(f"OpenRouter timeout: {resp.text}")
        if resp.status_code in (502, 503, 504):
            raise ModelUnavailableError(f"OpenRouter unavailable: {resp.text}")
        if resp.status_code == 400:
            raise ModelInvalidRequestError(f"OpenRouter bad request: {resp.text}")
        raise ModelError(f"OpenRouter error {resp.status_code}: {resp.text}")
