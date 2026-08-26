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


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model_policy=os.environ.get("MODEL_POLICY", "balanced"),
    )
