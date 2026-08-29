# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "can communicate with models" — all 5 sessions built (Level 2); construction-spec M1 code-complete
- **Current stage:** Stage 2 complete (model abstraction, registry, routing, retry/fallback) → Stage 3 (persistent project state) next
- **Current brick:** Session 5 (retry + fallback) built, Level 2 → Session 6 (Stage 3, project state) next
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
  `--model` now takes the usage path instead of being sent as the prompt.
- Session 4 — Routing (`core/models/routing.py`): `route(task_type,
  MODEL_POLICY) -> logical name`, small rule table, logged decision; CLI
  routes by `MODEL_POLICY` when `--model` omitted, prints selection. Level 2.
- Session 5 — Retry + fallback (`core/models/retry.py`): `call_with_retry`
  (capped exponential backoff, retryable errors only) + `generate_with_retry`
  (registry-resolved primary, one fallback logical model on retry-exhaustion);
  `Settings.model_fallback` (env `MODEL_FALLBACK`); CLI generate now goes
  through it (D008). Level 2.
- 46 unit tests total, all passing (level 2 — assistant sandbox)
- Full chain CLI → routing → registry → factory → provider → retry confirmed
  wired with injected fakes; real (non-injected) runs show the routing
  decision changing with MODEL_POLICY and a clean fast-fail with no key —
  still not run with a real key by the operator.

## In progress
- Verification level 3 pending for Sessions 2–5 — operator has not yet run
  the CLI with a real key.

## Blocked
- None.

## Decisions pending
- None new since D008.

## Next
- Operator: run `pytest -v` (expect 46 passed) and, with a real key in `.env`,
  `MODEL_POLICY=cheap python apps/cli/main.py "say hello"` then
  `MODEL_POLICY=quality ...` — confirm the printed selection / routing log line
  changes (Sessions 2–5 L3 in one go). This closes construction-spec
  Milestone 1 at Level 3.
- Then: Session 6 — Stage 3, Persistent Project State (Project Constitution).
  Per D006 the destination requires Postgres (Milestone C), skipping the
  spec's interim SQLite step — see BUILD_PLAN.md. Break out Session 6 in full
  session detail before starting (Construction Spec Part VII note).

## Last verified
Level 3 confirmed for Sessions 1 and 1b. Sessions 2, 3, 4, 5: level 2 only so far.
