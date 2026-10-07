
---

## File 4 — `docs/PROJECT_STATE.md`, `docs/progress.json`, `docs/ROADMAP.md`, `docs/DECISIONS.md`

These four were in my previous message with the exact content. If you already wrote them, skip. If not, they're still valid — re-paste from the previous message. Hash `8610b57` is already in `progress.json`.

**One small correction to make in `docs/PROJECT_STATE.md` if you wrote the version I sent:** the "Last verified" line should read `28.82s` (matches your actual run) and the milestone line should say "Sessions 6–8 built, Level 3" not "Sessions 6–7". Let me give the corrected `PROJECT_STATE.md` here for safety:

```markdown
# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 2 (Stage 3) — persistent project state on Postgres — Sessions 6–8 built, Level 3. Only S9 (CLI wiring + persist-across-runs proof) remains before Milestone C closes.
- **Current stage:** Stage 3 — Persistent Project State. DB seam + Constitution schema/migration + repository all in; CLI wiring next.
- **Current brick:** Session 8 (Constitution repository) built, Level 3 → Session 9 (CLI wiring) next
- **Build protocol:** non-negotiable build protocol in effect.

## Completed
- Session 1 — Model abstraction + Anthropic provider (Level 3)
- Session 1b — OpenRouter provider + minimal factory (Level 3, D004)
- Session 2 — CLI entrypoint (`apps/cli/main.py`) — Level 3
- Session 3 — Model registry (`core/models/registry.py`): logical names
  (`reasoning-strong`/`coding`/`cheap-fast`) → `(provider, model_id)`;
  provider-sourced capabilities; pure `estimated_cost()`;
  `ModelNotRegisteredError`; CLI gained `--model <logical-name>`; factory
  reused as the registry's construction primitive (D007). Level 3.
- CLI hardening (post-S3 review, commit `6c14d4b`): duplicate/leftover
  `--model` now takes the usage path instead of being sent as the prompt.
- Session 4 — Routing (`core/models/routing.py`): `route(task_type,
  MODEL_POLICY) -> logical name`, small rule table, logged decision; CLI
  routes by `MODEL_POLICY` when `--model` omitted, prints selection. Level 3.
- Session 5 — Retry + fallback (`core/models/retry.py`): `call_with_retry`
  (capped exponential backoff, retryable errors only) + `generate_with_retry`
  (registry-resolved primary, one fallback logical model on retry-exhaustion);
  `Settings.model_fallback` (env `MODEL_FALLBACK`); CLI generate now goes
  through it (D008). Level 3.
- Session 6 — DB access seam (`core/memory/db.py`): `connect()`/`ping()` over
  `DATABASE_URL`, lazy psycopg import, injectable connector; `MemoryError`
  hierarchy; `Settings.database_url`; `infra/docker-compose.yml` (pgvector);
  psycopg added to requirements. D009 (Postgres-first). Level 3.
- Session 7 — Constitution schema + migration: `core/memory/models.py`
  (13-field Constitution, Pydantic), `infra/migrations/0001_init.sql`
  (projects + constitutions, append-only/versioned/per-project),
  `core/memory/migrations.py` forward-only runner + `infra/migrate.py`. D010.
  Level 3.
- Session 8 — Constitution repository (`core/memory/constitution.py`):
  `create` / `get` / `get_version` / `append_change` / `history`. Append-only,
  versioned, per-project scoped (D010). Raises `ConstitutionNotFoundError`;
  never returns `None`. `change_history` owned by the repository; unknown
  field names rejected. `+1` for the next version computed in Python (D011).
  Credential redaction added to `core/memory/db.py` — driver error messages
  no longer leak URL passwords into tracebacks. Level 3 — operator verified
  against a live Supabase Postgres: 76 passed, 0 skipped. Commit `8610b57`.
- 76 tests passing, 0 skipped — Level 3, on the operator's machine.
-Session 9 — CLI `constitution` subcommands (`apps/cli/main.py`):
  `create` / `show` / `amend`, thin wrappers over `ConstitutionRepository`.
  Dispatch: `argv[1] == "constitution"` routes to the constitution handler;
  anything else routes to the chat path unchanged. `--set KEY=VALUE`
  repeatable, JSON-typed values. Errors caught (`MemoryError`, `ValueError`)
  and printed as one clean line. **Level 3 — operator verified: a
  Constitution created via the CLI survives a process boundary (run #1
  creates, run #2 reads back). Milestone C closed.**

## In progress
- None. Session 8 complete; ready for Session 9.

## Blocked
- None.

## Decisions pending
- None new since D011.

## Next
- Session 9 — CLI wiring + persist-across-runs proof:
  - `constitution create` / `constitution show` / `constitution amend`
    subcommands in `apps/cli/main.py`, thin over `ConstitutionRepository`
    (no logic in the CLI).
  - L2 test gate: CLI tests with an injected fake repository.
  - L3 milestone bar: create a Constitution in run #1 via the CLI, read it
    back in a separate run #2 (first locally, then against the cloud DB).
    This is the Milestone C definition of done.

## Last verified
Level 3 confirmed for Sessions 1, 1b, 2, 3, 4, 5, 6, 7, 8. Full suite:
76 passed, 0 skipped, 28.82s, on the operator's machine against a live
Supabase Postgres.
## Milestone D — Cloud API + Telegram bot (in progress)

**D1 — FastAPI cloud API skeleton — DONE (S10, L3).**
- `apps/api/__init__.py`, `apps/api/settings.py` (`ApiSettings` wrapper over
  `core.config.Settings`, per D014), `apps/api/app.py` (`create_app` +
  `GET /health` + module-level uvicorn app).
- `tests/test_api_health.py` — 2 tests, offline, injected settings.
- `requirements.txt` gained `fastapi` and `uvicorn[standard]`.
- L3 verified on the operator's machine: `uvicorn apps.api.app:app` served
  `/health` → `{"status":"ok"}`; `/docs` loaded.
- Full suite: 97 passed, 0 skipped (was 95 before D1).

**Next:** D2 (S11) — Telegram update parsing + allowlist auth.
**D2 — Telegram update parsing + allowlist auth — DONE (S11, L2).**
- `apps/api/telegram.py` — `IncomingMessage`, `parse_update`,
  `is_authorized`. Pure, offline-testable, never raises on malformed input.
- `apps/api/settings.py` extended — four Telegram fields on `ApiSettings`
  plus a masking `__repr__` (D013/D014 discipline). `load_api_settings()`
  reads `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS` (parsed to
  `tuple[int, ...]`), `TELEGRAM_WEBHOOK_SECRET`, `PUBLIC_BASE_URL`.
- `tests/test_telegram_auth.py` — fixture payloads only, no network.
- L3 deferred to D5 (real phone against deployed instance); D2 is L2 by design.

**D3 — Thin Telegram send_message client — DONE (S12, L2).**
- `apps/api/telegram.py` extended — `send_message(chat_id, text, settings, *,
  http=requests)`, `TelegramSendError`, and `_redact` (core redaction plus a
  Telegram-token-in-URL-path pass). Imports moved to top of file.
- `tests/test_telegram_send.py` — 8 tests, injected fake `http`, offline.
- No new env vars, no new routes. The webhook that calls this arrives in D4.
- L3 deferred to D5; D3 is L2 by design.
