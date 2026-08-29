# Build Plan — Phases, Order, and the Test Gate After Each

This file is the **ordered execution checklist** from where the build stands
today to the destination MVP (`PERSONAL_AI_OS_MASTER_ARCHITECTURE.md`,
Section 16). Every phase names **what it builds** and **the test that must
pass before it counts as done**. We execute it top to bottom: implement a
phase, run its test gate, verify, then move to the next — never skipping a
gate.

## How this file relates to the others (it does not override them)

- **Source of truth for *live status*** stays `docs/PROJECT_STATE.md` +
  `docs/progress.json`. This file is the *route and the gates*, not the
  status ledger. If they disagree on "what's done," PROJECT_STATE wins.
- **Source of truth for *what a phase means*** stays the authoritative specs:
  `00_MASTER_CONSTRUCTION_SPECIFICATION.md` (Part VI stage ladder, Part VII
  session detail) for the engine core, and
  `PERSONAL_AI_OS_MASTER_ARCHITECTURE.md` (Section 15 milestone sequence,
  Section 16 acceptance) for the cloud/phone destination. This file
  *reconciles and sequences* them; it does not restate their detail.
- **On any conflict, the destination doc governs** (per D006 and its own
  Section 0). The one live conflict is called out at Milestone C below.

## The execution loop (what "we begin, then test, then next" means)

For each phase, in order:

1. **Gate-in:** confirm every dependency is at **Level 3** in
   PROJECT_STATE.md. Per the destination's sequencing rule (Section 15), a
   phase does not start until its dependencies are operator-verified.
2. **Implement** the brick (small, single-purpose).
3. **Test (Level 2):** run the phase's automated test — must pass green with
   **no network and no real API key** required. This is the "test after each
   implementation."
4. **Verify (Level 3):** hand to the operator to run on their machine — and,
   from **Milestone C onward**, verified **from the phone against the
   deployed instance** (destination Section 14/16). Level 3 is the only level
   that counts as done.
5. **Record & commit:** only after Level 3, check the box here, update
   PROJECT_STATE/progress.json, and commit. Then proceed.

**Verification levels** (unchanged, from TESTING.md / destination Section 0):
`1 generated` (worth ~nothing) → `2 tested in the agent's sandbox` →
`3 verified by the operator` (the only level that counts).

## Status legend

`[x]` done & Level-3 verified · `[~]` built, Level-2 only (operator Level-3
pending) · `[ ]` not started · `NEXT` the immediate next brick.

---

## Milestone / stage crosswalk (three numbering schemes, reconciled)

| Destination milestone (Sec 15) | Construction-spec stage/session (Part VI/VII) | Repo ROADMAP milestone | Capability gained |
|---|---|---|---|
| **A** | Stage 0–1 · Sessions 1–2 | M1 (part) | Talk to a model, from a terminal |
| **B** | Stage 2 · Sessions 3–5 | M1 (rest) | Registry, policy routing, retry/fallback |
| **C** | Stage 3 (**Postgres, not SQLite** — see note) | M2 | Persistent project state that survives redeploy |
| **D** | *(destination-only)* Cloud API + Telegram | — | A phone message reaches the core and replies |
| **E** | Stage 4 (RAG on pgvector) | M3 | Grounded, cited answers over your documents |
| **F** | *(destination-only)* Job queue + workers | — | Long tasks finish while the phone is closed |
| **G** | Stage 5 (Tool system) | M4 | Agents can act via tools, sandboxed |
| **H** | Stage 6 (single-agent) | M5 | One agent completes a real task unattended |
| **I** | Stage 8–10 (Planner, task graph, Orchestrator) | M7–M8 | Objective → task graph → sequenced run |
| **J** | Stage 14 (Approval gates) | — | Approval-gated actions block/resume on phone |
| **K** | Stage 11 + 13 (multi-agent + verification) | M8 | Cooperating agents; creator ≠ verifier catches a break |
| **L** | Full loop (Section 16) | M9 | Phone-only MVP, no PC for normal use |

> **Live conflict, resolved:** the construction spec (Part IV, Stage 3) says
> `SQLite → PostgreSQL`. The destination doc (Milestone C) requires
> **PostgreSQL/pgvector from the start** (cloud-first). **The destination
> governs (D006):** we skip the SQLite step and build Milestone C directly on
> Postgres. Recorded here so it is a decision, not a silent deviation.

---

## Milestone A — Talk to a model (Sessions 1–2) — **DONE**

- `[x]` **Session 1 — Model abstraction + Anthropic provider.**
  Test gate: `pytest tests/test_anthropic_provider.py` → 4 pass, mocked
  client (L2); `python scripts/smoke_test.py` with a real key (L3).
  *Status: Level 3 (commit `5def786`).*
- `[x]` **Session 1b — OpenRouter provider + minimal factory (D004).**
  Test gate: `pytest tests/test_openrouter_provider.py tests/test_factory.py`
  → 10 pass, mocked (L2); `python scripts/smoke_test_openrouter.py` (L3).
  *Status: Level 3 (commit `3224fbf`).*
- `[~]` **Session 2 — CLI entrypoint (routes through the factory, D005).**
  Test gate: `pytest tests/test_cli.py` → 3 pass, injected fakes (L2);
  `python apps/cli/main.py "say hello"` with a real key (L3).
  *Status: Level 2 — operator Level-3 run still pending.*

**Milestone A gate:** ✅ `pytest -v` → 17 passed (confirmed). Operator
Level-3 for Session 2 is the one open item and is also the Session-3 gate-in.

---

## Milestone B — Registry, routing, retry (Sessions 3–5)

- `[~]` **Session 3 — Model registry (logical names → provider+model).**  *Built — Level 2*
  Built: `core/models/registry.py` (`ModelRegistry.resolve(logical_name)
  → (ModelProvider, model_id)`, `capabilities()` seeded from
  `ModelProvider.capabilities()`, `build_default_registry(settings)` reusing
  the existing factory, a pure `estimated_cost()` helper),
  `ModelNotRegisteredError`, and CLI `--model <logical_name>`.
  **Test gate (L2): ✅ `pytest -v` → 31 passed** — a known name resolves
  to the right `(provider, model_id)`; an unknown name raises
  `ModelNotRegisteredError` (a `ModelError`, **not** a `KeyError` leaking
  upward); `capabilities()` returns the provider's; `build_default_registry`
  honors `ACTIVE_PROVIDER`; `estimated_cost` math checks out — full suite
  green. **L3 (pending operator):** run `pytest -v` and
  `python apps/cli/main.py "say hello" --model reasoning-strong` with a real
  key. *(Spec: Part VII, Session 3; decision D007.)*
- `[~]` **Session 4 — Routing table + `MODEL_POLICY`.**  *Built — Level 2*
  Built: `core/models/routing.py` — `route(task_type, policy) → logical_name`
  over a small rule table (`general` fallback row + `code`), plus the
  routing-decision log line; CLI routes by `MODEL_POLICY` when `--model` is
  omitted and prints the selection in its stderr tag.
  **Test gate (L2): ✅ `pytest -v` → 39 passed** — the same task type under two
  policies resolves to two different logical names (`cheap`→`cheap-fast`,
  `quality`→`reasoning-strong`); every policy routes to a registered name;
  unknown task/policy fall back safely; the decision is logged. **L3 (pending
  operator):** with a real key, run the same prompt under `MODEL_POLICY=cheap`
  then `=quality` and see the printed selection / log line change. *(Spec: Part
  VII, Session 4. Note per D007: both resolve to one concrete model until a
  second is registered — the routing selection is what changes.)*
- `[~]` **Session 5 — Retry + fallback.**  *Built — Level 2*
  Built: `core/models/retry.py` — `call_with_retry` (capped exponential backoff
  for retryable errors only) + `generate_with_retry` (registry-resolved
  primary, one configured fallback logical model on retry-exhaustion);
  `Settings.model_fallback` (env `MODEL_FALLBACK`); CLI generate routed through
  it.
  **Test gate (L2): ✅ `pytest -v` → 46 passed** — fails-twice-then-succeeds
  returns; always-fails (retryable) triggers the fallback once; a non-retryable
  error fails fast with no retry and no fallback; backoff is 1s/2s (injected
  `sleep`, no real waiting). **L3 (pending operator):** exercised by any real
  CLI run; fallback is observable once `MODEL_FALLBACK` resolves to a different
  model (D008). *(Spec: Part VII, Session 5.)*

**Milestone B gate (destination Section 15):** registry resolves logical
names; the policy switch provably changes the model; retry survives a transient
failure. **Code-complete at Level 2** — closes construction-spec **Milestone 1**
pending the operator's Level-3 run.

---

## Milestone C — Persistent project state on Postgres

Broken into sessions in **`MILESTONE_C_PLAN.md`**. Summary status:

- `[~]` **Session 6 — DB access seam + config (D009).** *Built — Level 2.*
  `core/memory/db.py` (`connect`/`ping` over `DATABASE_URL`, lazy psycopg,
  injectable connector), `MemoryError` hierarchy, `Settings.database_url`,
  `infra/docker-compose.yml` (pgvector). **L2: ✅ 53 passed, 1 skipped** (live
  ping skips without a DB). **L3 (pending):** `docker compose up` + real ping.
- `[ ]` **Session 7 — Constitution schema + migration.** *Built — Level 2.*
  `core/memory/models.py` (13-field Constitution, Pydantic),
  `infra/migrations/0001_init.sql` (projects + constitutions; append-only,
  versioned, per-project), `core/memory/migrations.py` (forward-only runner) +
  `infra/migrate.py`. D010 (plain SQL, no Alembic). **L2: ✅ 59 passed, 2
  skipped.** L3: `python infra/migrate.py` against a real Postgres.
- `[ ]` **Session 8 — Constitution repository** (`core/memory/constitution.py`):
  create / read / **append-only** update (versioned, never in-place; per-project
  scoped). L2: integration test on a test DB, skips without one. L3: create+read
  from a shell.
- `[ ]` **Session 9 — CLI wiring + persist proof.** `constitution
  create/show/amend`. L2: CLI tests with an injected fake repo.
  **L3 = the milestone bar:** a Constitution created via the CLI **survives a
  redeploy** of the cloud instance (destination Milestone C).
- Depends on: **B (Level 3)**.

## Milestone D — Cloud API + Telegram bot (text-only)

- `[ ]` Builds: `apps/telegram/` (webhook handler, thin client only) and the
  minimal **FastAPI Cloud API** the destination requires (D003: core stays
  headless; Telegram ≈ CLI in weight). Deploy target stood up (Render/Fly),
  secrets in the host manager, webhook signature validated (Section 11).
  **Test gate (L2):** the webhook handler, given a fake Telegram update and a
  fake API, routes to the Orchestrator and formats a reply — unit-tested, no
  network. **L3:** a real message sent **from the phone** reaches the core and
  a reply returns to the phone (destination Milestone D).
- Depends on: **C (Level 3)**.

## Milestone E — Memory + RAG on Postgres/pgvector

- `[ ]` Builds: chunk → embed → store → retrieve pipeline on pgvector;
  closed-task summarization before embedding (Part XI).
  **Test gate (L2):** a question over a small ingested corpus returns a
  grounded answer **with a citation** (Stage 4 criterion), integration-tested.
  **L3:** the same, asked **from the phone**, returns a grounded, cited reply
  (destination Milestone E).
- Depends on: **C, D (Level 3)**.

## Milestone F — Job queue + background workers

- `[ ]` Builds: a Postgres-backed job queue and a separate `workers/` process
  that pulls, executes, **checkpoints progress**, and reports back; the Cloud
  API never blocks on a long task (Section 13).
  **Test gate (L2):** enqueue → worker executes → checkpoint written;
  killing a worker mid-task leaves a **resumable** state, not a lost one
  (Section 16). **L3:** a task dispatched **from the phone** completes after
  the phone app is closed and reopened (destination Milestone F).
- Depends on: **C, D (Level 3)**.

## Milestone G — Tool system (sandboxed)

- `[ ]` Builds: the `Tool` ABC (name, permission tier, input schema,
  `execute()` — Part XIII), initial tools (`web_search`, `read_file`, one
  external API), executed in a **sandboxed worker**; tool results treated as
  untrusted data (Part XX). New contract: `Tool` interface (add to CONTRACTS).
  **Test gate (L2):** an LLM-requested tool call executes and the result
  returns to the model (Stage 5 criterion); permission tiers enforced
  server-side; a prompt-injection attempt in a tool result is not
  re-interpreted as instructions. **L3:** an agent-initiated tool call
  executes in a worker and its result reaches the phone (destination
  Milestone G).
- Depends on: **E, F (Level 3)**.

## Milestone H — Single-agent execution, unattended

- `[ ]` Builds: one agent + tool loop returning the fixed agent **contract**
  (task, work, output, evidence, tests, failures, assumptions, risks, next
  action — Section 8). New contract: agent contract shape (add to CONTRACTS).
  **Test gate (L2):** given a bounded task, the agent loop produces a cited
  report / contract output with no manual step, using fake tools + a fake
  model (Stage 6 criterion). **L3:** the **scholarship-research example**
  (destination Section 2) completes end-to-end **from the phone**
  (destination Milestone H).
- Depends on: **F, G (Level 3)**.

## Milestone I — Planner + task graph + Orchestrator

- `[ ]` Builds: objective → questions → spec → **task graph**; the
  Orchestrator's "what runs next" dispatch respecting dependencies (Sections
  6, 8; Stages 8–10). New contract: task-graph node schema (add to CONTRACTS).
  **Test gate (L2):** a one-paragraph objective yields a task list a human
  recognizes as reasonable; independent tasks are identifiably parallel, a
  blocked task identifiably blocked; the Orchestrator sequences a fixed graph
  correctly (Stages 8–10 criteria). **L3:** a paragraph objective from the
  phone becomes a sane graph and a correctly sequenced multi-step run
  (destination Milestone I).
- Depends on: **E, H (Level 3)**.

## Milestone J — Approval gates, live on Telegram

- `[ ]` Builds: `approval_required` blocks dispatch; inline Telegram
  Approve/Reject/More-info buttons; a **pending-approval row in Postgres**
  that survives a worker restart (Section 12).
  **Test gate (L2):** an approval-gated action provably blocks until a
  response, then resumes; the pending record persists across a simulated
  restart (Stage 14 criterion). **L3:** the operator taps Approve/Reject on
  the phone and the branch blocks/resumes correctly (destination Milestone J).
- Depends on: **I (Level 3)**.

## Milestone K — Multi-agent + verification separation

- `[ ]` Builds: 2–3 specialized agents cooperating **through the
  Orchestrator** (no direct agent-to-agent dispatch, Section 6); creator ≠
  verifier enforced structurally in dispatch (Section 8; Stages 11, 13).
  **Test gate (L2):** a Researcher→Developer handoff happens with no manual
  context copy; a **deliberately broken** output is caught by the verifier,
  not by a human (Stages 11 & 13 criteria). **L3:** the operator observes both
  on a real task (destination Milestone K).
- Depends on: **I, J (Level 3)**.

## Milestone L — MVP: full loop, phone-only

- `[ ]` The terminal gate. All ten of the destination's **Section 16**
  acceptance criteria must be true, **verified from an actual phone against
  the deployed system**:
  1. `[ ]` A phone objective (text/voice) is acknowledged within seconds even
     if the task takes hours.
  2. `[ ]` It asks clarifying questions only when genuinely needed — not an
     interrogation.
  3. `[ ]` A multi-step task completes with the phone app closed for part of
     it; progress updates arrive unprompted.
  4. `[ ]` An approval-gated action blocks and resumes only after an explicit
     phone approval.
  5. `[ ]` The Adversarial/Critic mechanism produces a real
     "evidence-against-your-assumption" response at least once — not just
     agreement.
  6. `[ ]` A deliberately broken agent output is caught by verification before
     reaching the phone as finished.
  7. `[ ]` Killing a worker mid-task never silently loses it — it resumes or
     reports failure cleanly.
  8. `[ ]` "What's the status of X" and "what has this cost so far" answer
     accurately from the phone.
  9. `[ ]` Switching the active provider needs a config/env change only — no
     code change, no redeploy.
  10. `[ ]` None of the above required a terminal or the PC — the PC was only
      used to *build* the system.
- Depends on: **A–K (all Level 3)**.

---

## Post-MVP extensions (genuine extensions, not gaps — Section 16)

Sequenced after L, each with its construction-spec acceptance criterion:
browser/computer tools (Stage 12), deployment automation with
staging-auto / production-approval (Stage 15), observability + cost dashboard
(Stage 16 — note: cost hooks begin now via Session 3's `estimated_cost` and
`ModelResponse.total_tokens`, per Part XIX), self-improving workflows
(Stage 17, human-approved only; self-replication explicitly out of scope,
Part XXI), the general non-software execution loop (Stage 18), and further
interfaces (web dashboard, native app, full voice).

---

## Where we are right now

- **Done & Level-3:** Sessions 1, 1b. **Built, Level-2:** Sessions 2–7.
- **Baseline:** `pytest -v` → **59 passed, 2 skipped** (live DB ping + live
  migration; no network/keys).
- **Milestone B / construction-spec Milestone 1: code-complete at Level 2.**
  **Milestone C: DB seam (S6) + Constitution schema/migration (S7) in;**
  repository (S8) + CLI/persist-proof (S9) remain.
- **NEXT brick:** **Session 8 — Constitution repository** (create / read /
  append-only update). See MILESTONE_C_PLAN.md.
- **Milestones D–L:** deterministic build specs written ahead of time in
  `docs/MILESTONE_*_PLAN.md` (see `docs/BUILD_INSTRUCTIONS_INDEX.md`).
