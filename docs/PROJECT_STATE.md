# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "The system can communicate with models" — **COMPLETE**, pending Sessions 3-5 below (registry/routing/retry) which are still part of M1's original scope
- **Current stage:** Stage 1 — Basic AI interface (done) → moving toward Stage 2
- **Current brick:** Session 2 (CLI entrypoint) — next, spec below
- **Build protocol:** non-negotiable build protocol in effect.

## Completed
- Repository initialized
- Model interface (`ModelProvider`, `ModelResponse`, `ModelCapabilities`)
- Anthropic provider implementation
- OpenRouter provider implementation (dev/testing path, D004)
- Minimal provider factory/switch (`core/models/factory.py`, temporary — D004)
- 14 unit tests, all passing
- Both smoke test scripts written
- **Verification level 3 confirmed by operator** — tested and validated on
  their own machine, own credentials. This is the first brick to reach
  level 3.
- All six standing docs current

## Blocked
- None.

## Decisions pending
- None new since D004.

## Next
- Session 2 — CLI entrypoint + config hardening, updated to route through
  `core.models.factory.get_active_provider()` rather than hardcoding
  Anthropic, so the CLI respects whichever provider is currently active.

## Last verified
**Level 3 — confirmed by operator.**
