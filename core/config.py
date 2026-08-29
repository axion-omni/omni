"""
core/config.py — Stage 0 brick.

Single place the rest of the system reads configuration from. Nothing else
should call os.environ directly — this is the seam that lets Session 3+
add a proper settings/secrets system later without touching every caller.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    model_policy: str  # free | cheap | balanced | quality | maximum

    # --- added for OpenRouter dev/testing provider (no-credit unblock) ---
    # active_provider selects which ModelProvider core.models.factory hands
    # back. This is a minimal stopgap for Session 2's manual switching need
    # only — it gets superseded by the real Model Registry in Session 3,
    # which will do this by capability/cost instead of a flat env flag.
    active_provider: str  # "anthropic" | "openrouter"
    openrouter_api_key: str
    openrouter_model: str

    # --- Session 5: optional fallback logical model tried once if the primary
    # exhausts its retries on a retryable error. Empty means "no fallback".
    model_fallback: str


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model_policy=os.environ.get("MODEL_POLICY", "balanced"),
        active_provider=os.environ.get("ACTIVE_PROVIDER", "anthropic"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_model=os.environ.get(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
        ),
        model_fallback=os.environ.get("MODEL_FALLBACK", ""),
    )
