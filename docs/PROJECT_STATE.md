# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "The system can communicate with models" (in progress)
- **Current stage:** Stage 1 — Basic AI interface
- **Current brick:** Out-of-sequence addition complete (OpenRouter provider)
  → Session 2 (CLI entrypoint) still next
- **Build protocol:** non-negotiable build protocol in effect — docs are
  source of truth, Understand → Inspect → Plan → Implement → Test →
  Integrate → Verify → Document → Commit every session.

## Completed
- Repository initialized
- Model interface (`ModelProvider`, `ModelResponse`, `ModelCapabilities`)
- Anthropic provider implementation (untouched since Session 1)
- **OpenRouter provider implementation** (new — dev/testing path while no
  Anthropic credits available)
- **Minimal provider factory/switch** (`core/models/factory.py` — temporary,
  see DECISIONS.md D004)
- Unit tests: 14 total (4 Anthropic + 3 factory + 7 OpenRouter), all passing,
  all mocked (verification level 2)
- Smoke test scripts for both providers written (neither yet run against a
  real key/machine — verification level 3 still pending for both)
- All six standing docs current as of this update

## In progress
- Verification level 3 pending for both providers — operator has not yet
  confirmed `pytest -v` or either smoke test on their own machine.

## Blocked
- None. (OpenRouter path exists specifically because Anthropic credits are
  currently unavailable — this is noted, not a blocker for continued work.)

## Decisions pending
- None new since D004.

## Next
- Confirm this addition at verification level 3 (operator's machine, real
  OpenRouter key — free, no card needed).
- Then: Session 2 — CLI entrypoint + config hardening (ROADMAP.md).

## Last verified
Level 2 only (assistant's sandbox, all 14 tests). Level 3 not yet confirmed.
