"""
Tests for core.models.retry — proves retry/backoff and one-shot fallback with
no real waiting (sleep is injected) and no network or API key (level 2).

Session 5 acceptance (Master Construction Spec, Part VII):
  - a provider that fails twice then succeeds still returns a response;
  - a provider that always fails (retryable) triggers the fallback;
  - a non-retryable error fails fast with no retry.
"""

from __future__ import annotations

import pytest

from core.models.base import ModelResponse
from core.models.exceptions import (
    ModelAuthError,
    ModelInvalidRequestError,
    ModelRateLimitError,
    ModelUnavailableError,
)
from core.models.retry import call_with_retry, generate_with_retry


class _Recorder:
    """Records the delays passed to the injected sleep, so tests can assert the
    backoff schedule without ever actually sleeping."""

    def __init__(self):
        self.delays: list[float] = []

    def __call__(self, delay: float) -> None:
        self.delays.append(delay)


def _response(text="ok", model="m", provider="p"):
    return ModelResponse(
        text=text, model=model, provider=provider, input_tokens=1, output_tokens=1
    )


# --- call_with_retry -------------------------------------------------------

def test_succeeds_after_two_transient_failures():
    calls = {"n": 0}
    sleep = _Recorder()

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ModelUnavailableError("try again")
        return "done"

    result = call_with_retry(flaky, base_delay=1.0, sleep=sleep)

    assert result == "done"
    assert calls["n"] == 3
    assert sleep.delays == [1.0, 2.0]  # exponential backoff, 2 retries


def test_non_retryable_error_fails_fast_without_retry():
    calls = {"n": 0}
    sleep = _Recorder()

    def boom():
        calls["n"] += 1
        raise ModelAuthError("bad key")

    with pytest.raises(ModelAuthError):
        call_with_retry(boom, sleep=sleep)

    assert calls["n"] == 1  # tried once, never retried
    assert sleep.delays == []


def test_exhausts_attempts_then_reraises_original():
    calls = {"n": 0}
    sleep = _Recorder()

    def always_rate_limited():
        calls["n"] += 1
        raise ModelRateLimitError("slow down")

    with pytest.raises(ModelRateLimitError):
        call_with_retry(always_rate_limited, max_attempts=3, sleep=sleep)

    assert calls["n"] == 3  # first try + 2 retries
    assert sleep.delays == [1.0, 2.0]


# --- generate_with_retry (registry-aware, with fallback) -------------------

class _FakeProvider:
    def __init__(self, *, error=None, response=None):
        self._error = error
        self._response = response
        self.calls = 0

    def generate(self, prompt, **kwargs):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._response


class _FakeRegistry:
    def __init__(self, mapping: dict):
        # mapping: logical_name -> (provider, model_id)
        self._mapping = mapping
        self.resolved: list[str] = []

    def resolve(self, logical_name):
        self.resolved.append(logical_name)
        return self._mapping[logical_name]


def test_generate_falls_back_when_primary_exhausts_retries():
    primary = _FakeProvider(error=ModelUnavailableError("down"))
    fb = _FakeProvider(response=_response(text="from-fallback", provider="fb"))
    registry = _FakeRegistry(
        {"reasoning-strong": (primary, "m1"), "cheap-fast": (fb, "m2")}
    )
    sleep = _Recorder()

    result = generate_with_retry(
        registry,
        "hi",
        primary="reasoning-strong",
        fallback="cheap-fast",
        max_attempts=2,
        sleep=sleep,
    )

    assert result.text == "from-fallback"
    assert primary.calls == 2  # first + 1 retry, then gave up
    assert fb.calls == 1  # fallback tried once
    assert registry.resolved == ["reasoning-strong", "cheap-fast"]


def test_generate_does_not_fall_back_on_non_retryable_error():
    primary = _FakeProvider(error=ModelInvalidRequestError("malformed"))
    fb = _FakeProvider(response=_response(text="from-fallback"))
    registry = _FakeRegistry(
        {"reasoning-strong": (primary, "m1"), "cheap-fast": (fb, "m2")}
    )
    sleep = _Recorder()

    with pytest.raises(ModelInvalidRequestError):
        generate_with_retry(
            registry,
            "hi",
            primary="reasoning-strong",
            fallback="cheap-fast",
            sleep=sleep,
        )

    assert primary.calls == 1  # failed fast
    assert fb.calls == 0  # fallback never attempted
    assert "cheap-fast" not in registry.resolved


def test_generate_succeeds_on_primary_without_touching_fallback():
    primary = _FakeProvider(response=_response(text="primary-ok"))
    fb = _FakeProvider(response=_response(text="from-fallback"))
    registry = _FakeRegistry(
        {"reasoning-strong": (primary, "m1"), "cheap-fast": (fb, "m2")}
    )

    result = generate_with_retry(
        registry, "hi", primary="reasoning-strong", fallback="cheap-fast", sleep=_Recorder()
    )

    assert result.text == "primary-ok"
    assert fb.calls == 0
    assert registry.resolved == ["reasoning-strong"]


def test_generate_with_no_fallback_reraises_after_retries():
    primary = _FakeProvider(error=ModelRateLimitError("slow"))
    registry = _FakeRegistry({"reasoning-strong": (primary, "m1")})

    with pytest.raises(ModelRateLimitError):
        generate_with_retry(
            registry, "hi", primary="reasoning-strong", fallback=None, max_attempts=2, sleep=_Recorder()
        )

    assert primary.calls == 2
