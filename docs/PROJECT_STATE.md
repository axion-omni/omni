# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "can communicate with models" — Session 2 of 5 done
- **Current stage:** Stage 1 — Basic AI interface, moving toward Stage 2
- **Current brick:** Session 2 complete → Session 3 (model registry) next
- **Build protocol:** non-negotiable build protocol in effect.

## Completed
- Session 1 — Model abstraction + Anthropic provider (level 3 verified)
- Session 1b — OpenRouter provider + minimal factory (level 3 verified, D004)
- Session 2 — CLI entrypoint (`apps/cli/main.py`), routes through
  `factory.get_active_provider()` so it respects `ACTIVE_PROVIDER` —
  updated from the original spec per D004's downstream effect (see
  DECISIONS.md D005)
- 17 unit tests total, all passing (level 2 — assistant sandbox)
- CLI → factory → OpenRouter chain confirmed wired correctly end-to-end
  with a fake network layer (proves integration, not just unit-level
  correctness) — still not run with a real key by the operator

## In progress
- Verification level 3 pending for Session 2 specifically — operator has
  not yet run `python apps/cli/main.py "<prompt>"` with a real key.

## Blocked
- None.

## Decisions pending
- None new since D005.

## Next
- Operator: run `pytest -v` (expect 17 passed) and
  `python apps/cli/main.py "say hello"` with a real key (Anthropic or
  OpenRouter, whichever ACTIVE_PROVIDER points at) to confirm level 3.
- Then: Session 3 — Model registry (logical names → provider+model),
  per ROADMAP.md / Master Construction Spec Part VII.

## Last verified
Level 3 confirmed for Sessions 1 and 1b. Session 2: level 2 only so far.
