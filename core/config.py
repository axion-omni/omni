"""
core/config.py — Stage 0 brick, extended in S8.5 and (post-S9) with
credential-safe repr.

Single place the rest of the system reads configuration from. Nothing else
should call os.environ directly — this is the seam that lets Session 3+
add a proper settings/secrets system later without touching every caller.

Credential safety: Settings.__repr__ masks the password segment of
database_url so a pytest traceback (or any other place a Settings object
gets printed) never leaks it. The actual field value is unchanged — only
the repr is masked.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


# Matches `://user:password@` — the standard URL form.
_URL_CRED_RE = re.compile(r"(?<=://)([^:/@\s]+):([^@/\s]+)@")
# Matches any `:something@` — catches credentials outside a standard URL
# (concatenated URLs, unparsed fragments, etc.). Over-redacts by design:
# a redacted email is preferable to a leaked password.
_ANY_CRED_RE = re.compile(r":([^:/@\s]+)@")
# Matches `?password=...` or `password=...` / `pwd=` / `passwd=` key-value form.
_KV_CRED_RE = re.compile(r"(?i)\b(password|pwd|passwd)=([^&\s]+)")


def redact_credentials(text: str) -> str:
    """Replace password segments in a string with `***`. Used by Settings.__repr__
    and (via db.py) by exception messages, so credentials never reach a
    traceback, a log, or a test-failure dump.

    Three passes, in order:
      1. URL form       `://user:pass@` -> `://user:***@`
      2. Any-position   `:pass@`        -> `:***@`   (catches concatenated URLs)
      3. Key-value      `password=pass` -> `password=***`
    """
    text = _URL_CRED_RE.sub(lambda m: f"{m.group(1)}:***@", text)
    text = _ANY_CRED_RE.sub(":***@", text)
    text = _KV_CRED_RE.sub(lambda m: f"{m.group(1)}=***", text)
    return text


def _parse_model_overrides(raw: str) -> dict[str, str]:
    """Parse MODEL_OVERRIDES as JSON. Raise ValueError on malformed input.

    Rigid by design: a broken override blob fails at Settings construction,
    not at the first model call. Empty string → {}.
    """
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"MODEL_OVERRIDES is not valid JSON: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(
            "MODEL_OVERRIDES must be a JSON object mapping "
            "'provider:logical_name' to a model id string."
        )
    for k, v in parsed.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"MODEL_OVERRIDES entries must be string→string; got "
                f"{type(k).__name__}→{type(v).__name__} for key {k!r}."
            )
    return parsed


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    model_policy: str  # free | cheap | balanced | quality | maximum

    active_provider: str  # "anthropic" | "openrouter"
    openrouter_api_key: str
    openrouter_model: str

    model_fallback: str

    database_url: str = ""

    # --- S8.5: per-logical-name concrete model overrides ---
    # Keys are "${active_provider}:${logical_name}", e.g.
    # "openrouter:cheap-fast". Values are concrete model ids.
    model_overrides: dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Credential-safe repr — the ONLY reason this is hand-written.

        The default dataclass repr prints every field verbatim, including
        database_url's password. pytest tracebacks dump Settings, so a
        default repr leaks the DB password into test output. We mask the
        password in the repr while leaving the actual value intact.
        """
        return (
            "Settings("
            f"anthropic_api_key={'***' if self.anthropic_api_key else ''!r}, "
            f"model_policy={self.model_policy!r}, "
            f"active_provider={self.active_provider!r}, "
            f"openrouter_api_key={'***' if self.openrouter_api_key else ''!r}, "
            f"openrouter_model={self.openrouter_model!r}, "
            f"model_fallback={self.model_fallback!r}, "
            f"database_url={redact_credentials(self.database_url)!r}, "
            f"model_overrides={self.model_overrides!r}"
            ")"
        )


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
        database_url=os.environ.get("DATABASE_URL", ""),
        model_overrides=_parse_model_overrides(
            os.environ.get("MODEL_OVERRIDES", "")
        ),
    )
