"""
core/models/retry.py

Session 5 brick (Stage 2 — Model Abstraction & Routing): retry + fallback.
Completes Milestone 1 ("the system can communicate with models").

A transient failure — a rate limit, a timeout, a provider blip — should not
kill a run. This module adds two things on top of the registry (Session 3) and
routing (Session 4):

  1. call_with_retry(): capped exponential backoff (1s, 2s, 4s, ... by default)
     for RETRYABLE errors only. Auth/InvalidRequest/NotRegistered fail fast —
     retrying them wastes calls and money (CONTRACTS.md exception-hierarchy
     agreement).
  2. generate_with_retry(): resolves a *logical* model via the registry, calls
     generate() under retry, and — if the primary is still failing with a
     retryable error after its attempts are exhausted — tries a configured
     fallback logical model exactly once.

`sleep` is injected (defaults to time.sleep) so the unit tests exercise the
full backoff/fallback logic with zero real waiting.

Honest scope note (see DECISIONS.md D008): the retry mechanism is provider-
agnostic and complete. A *meaningful* fallback, however, needs the fallback
logical name to resolve to a different provider/model than the primary. Today
the registry builds a single active provider and maps every logical name to its
one default model (D007), so a live fallback resolves to the same place as the
primary and only helps once a second provider/model is registered. Retry itself
is immediately useful — it survives a transient error on the single provider,
which is exactly the Milestone 1 acceptance bar.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional, TypeVar

from core.models.base import ModelResponse
from core.models.exceptions import (
    ModelError,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)

logger = logging.getLogger("core.models.retry")

T = TypeVar("T")

# Only these are safe to retry automatically (CONTRACTS.md). Everything else —
# ModelAuthError, ModelInvalidRequestError, ModelNotRegisteredError — fails fast.
RETRYABLE_ERRORS: tuple[type[ModelError], ...] = (
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY = 1.0


def is_retryable_error(exc: BaseException) -> bool:
    """True only for the transient error types safe to retry."""
    return isinstance(exc, RETRYABLE_ERRORS)


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay: float = DEFAULT_BASE_DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call fn(); retry on retryable ModelErrors with exponential backoff.

    Delays are base_delay * 2**(attempt-1): 1s, 2s, 4s, ... A non-retryable
    error, or exhausting max_attempts, re-raises the original exception (never a
    wrapped/obscured one). max_attempts counts the first try, so max_attempts=3
    means at most 2 retries.
    """
    attempt = 0
    while True:
        try:
            return fn()
        except ModelError as exc:
            attempt += 1
            if not is_retryable_error(exc) or attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "retryable error %s (attempt %d/%d); backing off %.1fs",
                type(exc).__name__,
                attempt,
                max_attempts,
                delay,
            )
            sleep(delay)


def generate_with_retry(
    registry,
    prompt: str,
    *,
    primary: str,
    fallback: Optional[str] = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay: float = DEFAULT_BASE_DELAY,
    sleep: Callable[[float], None] = time.sleep,
    **generate_kwargs,
) -> ModelResponse:
    """Resolve `primary` via the registry and generate under retry; if it is
    still failing with a retryable error after its attempts are exhausted, try
    `fallback` once.

    A non-retryable failure (auth, malformed request, unknown model) fails fast
    and never triggers the fallback. If `fallback` is None or equal to
    `primary`, no fallback is attempted.
    """

    def attempt(logical_name: str) -> ModelResponse:
        provider, model_id = registry.resolve(logical_name)
        return call_with_retry(
            lambda: provider.generate(prompt, model=model_id, **generate_kwargs),
            max_attempts=max_attempts,
            base_delay=base_delay,
            sleep=sleep,
        )

    try:
        return attempt(primary)
    except ModelError as exc:
        if fallback and fallback != primary and is_retryable_error(exc):
            logger.warning(
                "primary '%s' exhausted (%s); trying fallback '%s'",
                primary,
                type(exc).__name__,
                fallback,
            )
            return attempt(fallback)
        raise
