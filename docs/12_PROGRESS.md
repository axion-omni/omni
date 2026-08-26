# Progress

Machine-readable state lives in `progress.json` (same directory).
This file is the human-readable view of the same state — keep them in sync.

## Overall
- **Current milestone:** Milestone 1 — "The system can communicate with models" (in progress)
- **Current stage:** Stage 1 — Basic AI interface
- **Current brick:** Session 1 (COMPLETE) → Session 2 (next)

## Completed bricks
- **Session 1 — Model abstraction + Anthropic provider.** `ModelProvider` ABC,
  `ModelResponse`/`ModelCapabilities` contracts, `AnthropicProvider`
  implementation, error translation, 4 passing unit tests (mocked client,
  no network/key required). Live smoke test script written, not yet run
  against a real key.

## Next brick
- **Session 2 — Config hardening + CLI entrypoint.** Wire `core/config.py`
  into a minimal `cli.py` that takes a prompt as an argv and prints the
  response, using the real provider. This is the first moment the system
  does something end-to-end from a terminal command instead of from tests.

## Blocked
- None.

## Open questions
- None yet — will accumulate as Stage 2 (model registry / routing) begins.

## Open risks
- None yet.

## Failed experiments
- None yet.
