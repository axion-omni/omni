"""
scripts/smoke_test_openrouter.py

Run by hand after putting a real OPENROUTER_API_KEY in .env and setting
ACTIVE_PROVIDER=openrouter:

    python scripts/smoke_test_openrouter.py

Hits the real OpenRouter API (free tier — should cost $0, but is still a
real network call, not part of the pytest suite).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import load_settings
from core.models.providers.openrouter_provider import OpenRouterProvider


def main():
    settings = load_settings()
    if not settings.openrouter_api_key or "your-key-here" in settings.openrouter_api_key:
        print("No real OPENROUTER_API_KEY found in .env — add one first.")
        print("Get a free key at https://openrouter.ai/keys (no card required).")
        sys.exit(1)

    provider = OpenRouterProvider(
        api_key=settings.openrouter_api_key,
        default_model=settings.openrouter_model,
    )
    result = provider.generate(
        "Reply with exactly the words: brick one works.",
        max_tokens=20,
    )
    print(f"Model:    {result.model}")
    print(f"Response: {result.text!r}")
    print(f"Tokens:   {result.input_tokens} in / {result.output_tokens} out (cost: $0, free tier)")

    assert "brick one works" in result.text.lower(), "Unexpected response — check manually."
    print("\nSmoke test passed. OpenRouter provider is confirmed live and free.")


if __name__ == "__main__":
    main()
