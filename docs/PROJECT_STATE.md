# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "can communicate with models" — Sessions 3–4 of 5 built (Level 2)
- **Current stage:** Stage 2 — Model abstraction & routing (registry + routing done; retry/fallback next)
- **Current brick:** Session 4 (routing table + MODEL_POLICY) built, Level 2 → Session 5 (retry + fallback) next
- **Build protocol:** non-negotiable build protocol in effect.

## Completed
- Session 1 — Model abstraction + Anthropic provider (level 3 verified)
- Session 1b — OpenRouter provider + minimal factory (level 3 verified, D004)
- Session 2 — CLI entrypoint (`apps/cli/main.py`) — level 2 (operator L3 pending)
- Session 3 — Model registry (`core/models/registry.py`): logical names
  (`reasoning-strong`/`coding`/`cheap-fast`) → `(provider, model_id)`;
  provider-sourced capabilities; pure `estimated_cost()`;
  `ModelNotRegisteredError`; CLI gained `--model <logical-name>`; factory
  reused as the registry's construction primitive (D007). Level 2.
- CLI hardening (post-S3 review, commit `6c14d4b`): duplicate/leftover
  `--model` now takes the usage path instead of being sent as the prompt;
  2 regression tests.
- Session 4 — Routing (`core/models/routing.py`): `route(task_type,
  MODEL_POLICY) -> logical name`, small rule table (`general` fallback row +
  `code`), logged decision; CLI now routes by `MODEL_POLICY` when `--model`
  is omitted and prints the selection in its stderr tag. Level 2.
- 39 unit tests total, all passing (level 2 — assistant sandbox)
- CLI → routing → registry → factory → provider chain confirmed wired
  end-to-end with injected fakes, plus a real (non-injected) run showing the
  routing decision change with MODEL_POLICY (cheap→cheap-fast,
  quality→reasoning-strong) — still not run with a real key by the operator.

## In progress
- Verification level 3 pending for Sessions 2, 3, and 4 — operator has not
  yet run the CLI with a real key.

## Blocked
- None.

## Decisions pending
- None new since D007. (Session 4 introduced no new decision; the
  one-model-per-provider consequence is already covered by D007.)

## Next
- Operator: run `pytest -v` (expect 39 passed) and, with a real key in `.env`,
  `MODEL_POLICY=cheap python apps/cli/main.py "say hello"` then
  `MODEL_POLICY=quality python apps/cli/main.py "say hello"` — confirm the
  printed selection / routing log line changes (Session 4 L3), which also
  covers Sessions 2–3's pending L3.
- Then: Session 5 — Retry + fallback (`core/models/retry.py`): backoff for
  retryable errors only, one configured fallback — completes Milestone 1.

## Last verified
Level 3 confirmed for Sessions 1 and 1b. Sessions 2, 3, 4: level 2 only so far.
