# Decision Log

Append-only. Never edit a past entry — if a decision is reversed, add a new
entry that references the old one.

---

### D001 — Language: Python for the engine core
**Date:** Session 1
**Decision:** Python 3.12 for `core/`, `agents/`, `tools/`, orchestrator.
**Why:** The AI-systems ecosystem (agent frameworks, RAG libraries, provider
SDKs, eval tooling) is deepest in Python. Go and Dart remain the right
choice for C-Transit/NEXA's own product surfaces, not for this engine.
**Alternative considered:** TypeScript/Node — rejected only for the core
engine because the agent-framework ecosystem (LangGraph, CrewAI-equivalents)
is thinner there today. Revisit if a future UI layer wants a Node backend —
that's a separate service, not a rewrite of this one (see D003).
**Reversible:** Yes, if provider abstraction (D002) is respected, swapping
the orchestrator language later doesn't require rewriting provider code.

### D002 — Provider abstraction boundary
**Date:** Session 1
**Decision:** No file outside `core/models/providers/` may import a
provider SDK directly. All access goes through `ModelProvider`.
**Why:** This is the single control that prevents permanent lock-in to
Anthropic specifically — a new provider is a new file implementing the
interface, not a rewrite.
**Reversible:** N/A — this is a standing rule, not a one-time choice.

### D003 — Core engine stays headless
**Date:** Session 1 (documented in advance, enforced starting Stage 15/UI)
**Decision:** The engine exposes itself over an API from the start. No UI
framework gets imported into `core/`.
**Why:** Part XV of the master architecture requires the same underlying
system to be reachable from PC, phone, browser, and Telegram without
duplicated logic. Retrofitting this later is expensive; it's nearly free
if respected from Session 1 onward.

### D004 — OpenRouter added as a second provider, ahead of the Session 3 registry
**Date:** post-Session 1, pre-Session 2
**Decision:** Added `OpenRouterProvider` (implements the existing
`ModelProvider` interface) plus a minimal `core/models/factory.py` that
switches between it and `AnthropicProvider` via one env var
(`ACTIVE_PROVIDER`). Default model: `meta-llama/llama-3.3-70b-instruct:free`.
**Why:** No Anthropic API credits currently available for local testing.
This unblocks development without waiting on funding, and without touching
the Anthropic path at all.
**What was NOT touched:** `core/models/providers/anthropic_provider.py` —
zero lines changed. `AnthropicProvider` remains the default
(`ACTIVE_PROVIDER=anthropic`) and is fully intact for when credits return.
**Scope note:** `factory.py` is intentionally minimal — a flat env-var
switch, not the capability/cost-aware Model Registry planned for Session 3
in ROADMAP.md. It exists to unblock testing today; Session 3 absorbs or
replaces it. This is a known, logged overlap, not an accidental duplication.
**Reversible:** Yes — switching back to Anthropic-only requires no code
change, just `ACTIVE_PROVIDER=anthropic` (already the default).

### D005 — CLI routes through the factory, not a hardcoded provider
**Date:** Session 2
**Decision:** `apps/cli/main.py` calls
`core.models.factory.get_active_provider(settings)`, never constructs
`AnthropicProvider` directly, even though the original Session 2 spec
(written before D004/OpenRouter existed) assumed the latter.
**Why:** Hardcoding the CLI to Anthropic would silently ignore
`ACTIVE_PROVIDER` and defeat the point of D004 — the CLI is the first real
consumer of the provider switch, so it has to actually use it.
**Reversible:** Yes — no different than any other factory consumer.

### D006 — Destination expanded to a phone-first, cloud-first Personal AI OS
**Date:** post-Session 2, pre-Session 3 (handoff point)
**Decision:** The project's destination architecture is now
`PERSONAL_AI_OS_MASTER_ARCHITECTURE.md` — a superset of the original
`AI_Project_Execution_Engine.md`, adding: Telegram/phone interface, cloud
deployment as the normal runtime (not the PC), async job queue + background
workers, and a revised milestone sequence (Milestones A–L) that maps
Sessions 1–2 (already done) onto Milestones A and part of B.
**Why:** The original destination assumed a local, synchronous, terminal-
operated system. The actual intent was always a remotely-usable system —
this decision formalizes that and gives it a concrete architecture instead
of leaving it implicit.
**What was NOT invalidated:** every existing contract (`ModelProvider`,
the exception hierarchy, the factory pattern, the six-doc structure, the
build protocol itself) carries forward unchanged. This is an extension of
scope, not a redesign of what's built.
**Reversible:** The cloud/phone layers are additive on top of `core/` —
if this direction changed again, `core/` would not need to be rewritten.

### D007 — Model Registry is the caller-facing layer; the factory is retained as its construction primitive
**Date:** Session 3
**Decision:** Built `core/models/registry.py` (`ModelRegistry`, `resolve() ->
(ModelProvider, model_id)`, provider-sourced `capabilities()`,
`build_default_registry()`, pure `estimated_cost()`), per Master Construction
Spec Part V / Part VII Session 3. Callers (starting with the CLI) now resolve
models through the registry using **logical names** (`reasoning-strong`,
`coding`, `cheap-fast`), never a raw provider/model string.
**On "replacing the temporary factory.py":** the factory was **not deleted**.
`build_default_registry()` calls `factory.get_active_provider()`, so
`ACTIVE_PROVIDER` selection + key handling live in exactly one place and D004's
no-Anthropic-credit dev route is preserved untouched. The factory's role
narrowed from "what callers use" to "how the registry constructs the active
provider." Deleting it would have forced that selection logic to be duplicated
inside the registry for no benefit and would have churned `test_factory.py`.
This realizes CONTRACTS.md's predicted "migrate callers to the registry"
without a rewrite of working, tested code.
**Scope kept small (Part VII, Session 3):** capabilities are sourced from
`ModelProvider.capabilities()`, not duplicated in a second table. Only one
verified model exists per provider today, so every logical name resolves to the
active provider's default model; the task-type + `MODEL_POLICY` routing table
that makes them diverge is **Session 4**, and retry/fallback is **Session 5** —
both deferred deliberately, not forgotten.
**On the destination doc's "queryable for cost" addition (Section 9):**
satisfied at the per-call level now via `estimated_cost()` +
`ModelCapabilities.cost_per_million_*` (justified from Stage 2 onward by Spec
Part XIX). The persistent per-project cost-to-date total is deferred to the
event log / Observability (Stage 16), because no persistence layer exists yet —
building a ledger now would be speculative.
**New error type:** `ModelNotRegisteredError(ModelError)` — an unknown logical
name is a clean, catchable model-layer error, not a `KeyError` leaking upward.
**Reversible:** Yes — the registry is additive; the factory contract is
unchanged, so reverting to calling the factory directly would be mechanical.

### D008 — Retry is provider-agnostic and complete; a live fallback needs a second registered model
**Date:** Session 5
**Decision:** Built `core/models/retry.py` with `call_with_retry()` (capped
exponential backoff, retryable errors only) and `generate_with_retry()`
(resolve a logical model via the registry, generate under retry, try one
configured fallback logical model if the primary exhausts retries on a
retryable error). Added `Settings.model_fallback` (env `MODEL_FALLBACK`,
default empty). The CLI's generate call now goes through `generate_with_retry`.
**Retryable set (honors CONTRACTS.md):** only `ModelRateLimitError`,
`ModelTimeoutError`, `ModelUnavailableError` are retried. `ModelAuthError`,
`ModelInvalidRequestError`, and `ModelNotRegisteredError` fail fast — retrying
them wastes calls and money.
**Honest limitation, stated not hidden:** the retry loop is fully useful today
(it survives a transient error on the single active provider — the Milestone 1
bar). The *fallback*, however, only changes the outcome once the fallback
logical name resolves to a different provider/model than the primary. Because
the registry currently builds one active provider and maps every logical name
to its single default model (D007), a live fallback resolves to the same place
as the primary. The mechanism is complete and unit-proven with distinct fake
providers; wiring a genuinely different fallback model is unblocked the moment a
second provider/model is registered — no code change to retry.py required.
**`sleep` is injected** (defaults to `time.sleep`) so the automated tests prove
the full backoff/fallback logic with zero real waiting.
**Reversible:** Yes — retry wraps the existing generate call; removing it
returns to a direct `provider.generate()` with no contract change.

### D009 — Persistence is PostgreSQL from the start (no SQLite step); DB access behind a seam
**Date:** Session 6 (Milestone C)
**Decision:** Build the persistence layer directly on PostgreSQL, skipping the
construction spec's interim SQLite stage (Part IV / Stage 3). Introduced
`core/memory/` with a single database access seam (`core/memory/db.py`,
`connect()`/`ping()`) that turns `DATABASE_URL` into a connection — nothing else
imports the Postgres driver. Added `Settings.database_url` (env `DATABASE_URL`,
default empty) and `infra/docker-compose.yml` (pgvector image) for local dev.
**Why:** the destination (D006, Milestone C) requires project state to survive a
**cloud redeploy**. SQLite on a local disk does not survive a Render redeploy,
so building the SQLite step first would be throwaway work. The same Postgres
instance also carries into Milestone E's pgvector RAG — one backend, not two.
**Generalizes D002 to storage:** just as provider SDKs live only in
`core/models/providers/`, the DB driver lives only in `core/memory/`, keeping
the backend swappable (Part XXII).
**What was NOT changed:** model layer, CLI chat path, exception hierarchy.
`Settings` gained one trailing defaulted field, so existing constructors are
untouched. `psycopg` is imported lazily (like the `anthropic` SDK), so the test
suite needs neither the driver nor a live database — DB-touching tests skip when
`DATABASE_URL` is unset.
**Consequence for dev:** local development now needs a Postgres — Docker via
`infra/docker-compose.yml`, or a dev-tier managed instance.
**Reversible:** Yes — the seam + repository pattern confine a backend change to
`core/memory/`, not callers.
