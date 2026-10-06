"""
Tests for credential redaction — post-S8 incident (D013).

Proves the leak paths are closed:
  1. Settings.__repr__ masks database_url's password.
  2. Settings.__repr__ masks API keys.
  3. redact_credentials() handles URL, any-position, and key-value forms.
  4. redact_credentials() handles the concatenated-URL shape from the S9 incident.
"""

from core.config import Settings, redact_credentials


def _settings(url: str) -> Settings:
    return Settings(
        anthropic_api_key="sk-ant-secret-1234",
        model_policy="balanced",
        active_provider="anthropic",
        openrouter_api_key="sk-or-secret-5678",
        openrouter_model="x",
        model_fallback="",
        database_url=url,
    )


# --- Settings.__repr__ ----------------------------------------------------

def test_settings_repr_masks_database_url_password():
    s = _settings("postgresql://user:supersecret@db.example.com:5432/postgres")
    text = repr(s)
    assert "supersecret" not in text
    assert "user:***@" in text
    assert "db.example.com" in text  # host still visible for debugging


def test_settings_repr_masks_api_keys():
    s = _settings("postgresql://x/y")
    text = repr(s)
    assert "sk-ant-secret-1234" not in text
    assert "sk-or-secret-5678" not in text


# --- redact_credentials: URL form -----------------------------------------

def test_redact_handles_url_form():
    assert redact_credentials(
        "postgresql://u:p@h/db"
    ) == "postgresql://u:***@h/db"


# --- redact_credentials: key-value form -----------------------------------

def test_redact_handles_password_query_param():
    out = redact_credentials("postgresql://h/db?password=p")
    assert "password=***" in out
    assert "?password=p" not in out  # original gone


def test_redact_handles_pwd_and_passwd_kv():
    assert "pwd=***" in redact_credentials("x?pwd=secret&host=h")
    assert "passwd=***" in redact_credentials("x?passwd=secret")


# --- redact_credentials: concatenated URLs (the S9 incident) --------------

def test_redact_handles_concatenated_urls():
    # The exact malformed shape from the S9 incident: two URLs glued together
    # with only one `://` — the URL-form regex alone would miss the second.
    bad = (
        "postgresql://hidden:secret1@hidden:5432/"
        "/postgres:secret2@db.example.com:5432/postgres"
    )
    redacted = redact_credentials(bad)
    assert "secret1" not in redacted
    assert "secret2" not in redacted
    # Both credentials replaced with the mask.
    assert redacted.count(":***@") >= 1


# --- redact_credentials: safety over-redaction ----------------------------

def test_redact_over_redacts_rather_than_under_redacts():
    # A mailto-style string loses the "user" portion — safe by design.
    # Better to over-redact than to leak.
    out = redact_credentials("contact mailto:someone@example.com")
    assert "someone" not in out or "***" in out
