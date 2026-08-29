# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 2 (Stage 3) — persistent project state on Postgres — started (Session 6 of ~9 built, Level 2). Milestone 1 code-complete (L2).
- **Current stage:** Stage 3 — Persistent Project State. DB access seam in; schema/repository/CLI next.
- **Current brick:** Session 6 (DB access seam + config, D009) built, Level 2 → Session 7 (Constitution schema + migration) next
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
- Session 6 — DB access seam (`core/memory/db.py`): `connect()`/`ping()` over
  `DATABASE_URL`, lazy psycopg import, injectable connector; `MemoryError`
  hierarchy; `Settings.database_url`; `infra/docker-compose.yml` (pgvector);
  psycopg added to requirements. No schema yet. D009 (Postgres-first). Level 2.
- 53 unit tests passing, 1 skipped (live DB ping) — level 2, assistant sandbox.
- Full chain CLI → routing → registry → factory → provider → retry confirmed
  wired with injected fakes; real (non-injected) runs show the routing
  decision changing with MODEL_POLICY and a clean fast-fail with no key —
  still not run with a real key by the operator.

## In progress
- Verification level 3 pending for Sessions 2–5 (CLI with a real key) and
  Session 6 (live Postgres ping) — operator has not yet run either.

## Blocked
- None.

## Decisions pending
- None new since D009.

## Next
- Operator (optional, anytime): Sessions 2–5 L3 — `pytest -v` (expect 53
  passed, 1 skipped) + real-key CLI under two `MODEL_POLICY` values.
- Operator Session 6 L3: `docker compose -f infra/docker-compose.yml up -d`,
  set `DATABASE_URL` in `.env`, run `pytest -v` and see the previously-skipped
  `test_ping_live_database` pass.
- Then: Session 7 — Constitution schema + migration (see MILESTONE_C_PLAN.md).

## Last verified
Level 3 confirmed for Sessions 1 and 1b. Sessions 2, 3, 4, 5, 6: level 2 only so far.
