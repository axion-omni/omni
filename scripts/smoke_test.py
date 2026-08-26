"""
scripts/smoke_test.py

Run this by hand after you've put a real key in .env:

    python scripts/smoke_test.py

This hits the real network and real API — it's not part of `pytest` on
purpose (CI shouldn't spend money or depend on network availability).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import load_settings
from core.models.providers.anthropic_provider import AnthropicProvider


def main():
    settings = load_settings()
    if not settings.anthropic_api_key or "your-key-here" in settings.anthropic_api_key:
        print("No real ANTHROPIC_API_KEY found in .env — add one first.")
        sys.exit(1)

    provider = AnthropicProvider(api_key=settings.anthropic_api_key)
    result = provider.generate(
        "Reply with exactly the words: brick one works.",
        max_tokens=20,
    )
    print(f"Model:    {result.model}")
    print(f"Response: {result.text!r}")
    print(f"Tokens:   {result.input_tokens} in / {result.output_tokens} out")

    assert "brick one works" in result.text.lower(), "Unexpected response — check manually."
    print("\nSmoke test passed. Stage 1 brick is confirmed live.")


if __name__ == "__main__":
    main()
