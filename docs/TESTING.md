# Testing

## Strategy

| Test type | Covers | Status in this repo |
|---|---|---|
| Unit | One function/class, dependencies mocked | 4 tests, `tests/test_anthropic_provider.py` |
| Integration | Real components talking to each other | None yet — needed from Session 6+ (state + memory) |
| Failure | Deliberately broken input/dependency | 2 of the 4 current tests are failure-path tests |
| Security | Injection, permission bypass | Needed from the Tool System onward (Session ~9+) |
| AI behavior | Output meets quality criteria, not just "ran" | Needed from Session ~11+ (agent evaluation) |
| Regression | A fixed bug stays fixed | Add per-bug starting whenever the first bug is found |

## Current test suite

```
pytest -v
```
Expected: `4 passed`, no network or API key required (client is mocked via
`client_factory` injection — see `tests/test_anthropic_provider.py`).

## Live verification (separate from automated tests, on purpose)

```
python scripts/smoke_test.py
```
Requires a real `ANTHROPIC_API_KEY` in `.env`. Hits the real network and
costs a small amount of real money. Not run by CI or by default — this is
the "Level 3" check per the build protocol: proof the system works on your
actual machine with your actual credentials, not just proof the mocked
contract holds.

## Verification levels (per project protocol)

1. **Generated** — code exists, unverified. Worth nothing on its own.
2. **Tested in the AI's environment** — the assistant ran `pytest` and it
   passed there.
3. **Verified on your machine** — you ran `pytest -v` and `smoke_test.py`
   yourself. **This is the only level that counts as "done."**

No brick is marked complete in PROJECT_STATE.md until it has reached level 3.

## OpenRouter provider tests (added post-Session 1)

```
pytest -v
```
Now runs 14 tests total (4 Anthropic + 3 factory + 7 OpenRouter), all
mocked — no network or API key required for the automated suite.

## Live verification for OpenRouter (separate, real network, still $0)

```
python scripts/smoke_test_openrouter.py
```
Requires a real `OPENROUTER_API_KEY` in `.env` (free, no card, from
https://openrouter.ai/keys) and `ACTIVE_PROVIDER=openrouter`. This is the
level-3 check for the OpenRouter path specifically — running it does not
verify the Anthropic path, and vice versa. Both smoke tests are independent;
neither is run by `pytest` or CI.

## CLI tests (Session 2)

`pytest -v` runs the CLI tests with mocked injection (`registry_builder`,
`settings_loader`) — same pattern as every provider test — so no env vars or
network are touched by the automated suite.

Manual end-to-end check (not part of pytest): with a real key in `.env`,
```
python apps/cli/main.py "say hello"
```
should print a real model response.

## Model registry tests (Session 3)

`pytest -v` now runs **31 tests** (17 prior + 11 registry + 3 net-new CLI),
all mocked — no network or API key required. `tests/test_registry.py` proves:
a known logical name resolves to the right `(provider, model_id)`; an unknown
name raises `ModelNotRegisteredError` (a `ModelError`, **not** a `KeyError`);
`capabilities()` is sourced from the provider for the resolved model;
`estimated_cost()` arithmetic; and `build_default_registry()` honors
`ACTIVE_PROVIDER` (Anthropic default, OpenRouter switch, fail-fast on unknown).

Manual end-to-end check (not part of pytest): with a real key in `.env`,
```
python apps/cli/main.py "say hello" --model reasoning-strong
```
should print a real model response, tagged with the resolved provider/model.
This is the **Level-3** check for Session 3.

## Routing tests (Session 4)

`pytest -v` now runs **39 tests** (33 prior + 6 routing). `tests/test_routing.py`
proves the Session 4 acceptance criterion — the same task type under two
policies routes to two different logical names (`cheap` → `cheap-fast`,
`quality` → `reasoning-strong`) — plus: every policy routes to a registered
logical name; unknown task_type falls back to the `general` row; unknown policy
falls back to the default; and the routing decision is logged. All mocked, no
network or key.

Manual end-to-end check (not part of pytest): the routing decision is logged
and printed in the CLI's stderr tag. With a real key in `.env`, flip the policy
and see the selection change for an identical prompt:
```
MODEL_POLICY=cheap    python apps/cli/main.py "say hello"
MODEL_POLICY=quality  python apps/cli/main.py "say hello"
```
The `[... — policy=<policy> -> <logical>]` tag (and the `core.models.routing`
log line) is the **Level-3** proof for Session 4. Note: until a second concrete
model is registered (D007), both resolve to the same provider model — the
*routing selection* is what visibly changes.

## Retry + fallback tests (Session 5)

`pytest -v` now runs **46 tests** (39 prior + 7 retry). `tests/test_retry.py`
proves the Session 5 acceptance criteria with an injected `sleep` (no real
waiting) and no network: a provider that fails twice then succeeds still
returns; a provider that always fails with a retryable error triggers the
fallback once; a non-retryable error (auth/invalid) fails fast with no retry
and never triggers the fallback; backoff follows 1s/2s. All mocked.

Manual note: retry/fallback have no dedicated live smoke test — a transient
provider error is not reliably reproducible on demand. The retry path is
exercised implicitly by any real CLI run; the fallback becomes observable once
`MODEL_FALLBACK` resolves to a genuinely different model (D008).

## Memory / DB seam tests (Session 6)

`pytest -v` now runs **53 tests, 1 skipped**. `tests/test_db.py` proves config
reads `DATABASE_URL`, `connect()` fails clearly when it is empty
(`DatabaseNotConfiguredError`), driver errors are translated
(`DatabaseConnectionError`), and `connect()/ping()` work through an **injected
fake connector** — so the suite needs neither the `psycopg` driver nor a live
database. The single live check, `test_ping_live_database`, **skips** unless
`DATABASE_URL` is set.

**Level-3 (operator):**
```
docker compose -f infra/docker-compose.yml up -d      # local Postgres (pgvector)
# put DATABASE_URL=postgresql://engine:engine@localhost:5432/engine in .env
pytest -v        # test_ping_live_database now runs and passes (52+2 = 53 run)
```
This confirms the seam connects to a real Postgres — the gate before Session 7's
schema.

## Schema tests (Session 7)

`pytest -v` now runs **59 tests, 2 skipped**. `tests/test_schema.py` proves the
`Constitution` model has exactly the 13 sections, defaults empty, and JSON
round-trips; migration discovery finds `0001_init` and `pending()` filters
applied versions; and `run()` applies migrations against an **injected fake
connection** (no DB). The live apply, `test_run_against_live_database_is_
idempotent`, **skips** without `DATABASE_URL`.

**Level-3 (operator):** after `docker compose up`, `python infra/migrate.py`
creates the tables; a second run reports "already up to date"; `pytest -v` then
runs the two previously-skipped live tests.
