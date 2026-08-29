# Milestone C — Persistent Project State (Postgres): Session Plan

**Status of this document:** proposed session breakdown for Milestone C, for
operator approval **before** any code. Follows the standing build protocol
(Understand → Inspect → Plan → Implement → Test → Integrate → Verify →
Document → Commit) and the three-level verification discipline. Nothing here is
built yet.

## What Milestone C is (and is not)

**Deliverable (destination Section 15):** a **Project Constitution** created via
the CLI **survives a redeploy** of the cloud instance. Construction-spec Stage 3
criterion, tightened for cloud: the Constitution is created, read, and updated
across **two separate process runs** — and, at Level 3, across a **Render
redeploy**.

**Is:** the first persistence layer — a real, queryable Project Constitution in
**PostgreSQL** (per D006, skipping the spec's interim SQLite step), behind a
repository interface so the DB is swappable (Spec Part XXII).

**Is not:** the phone layer (that's D), vectors/RAG (that's E), tools, or
agents. No `apps/telegram/`, no FastAPI yet. This milestone is still driven from
the CLI.

## The one decision this milestone forces (needs a decision-log entry)

**D009 (proposed) — Postgres from the start, no SQLite step.** The construction
spec says `SQLite → Postgres`; the destination (Milestone C) requires Postgres
because state must survive a cloud redeploy. We build directly on Postgres. This
is already flagged in BUILD_PLAN.md; Session 6 will make it a formal D009 entry.
Consequence: local development needs a Postgres too (Docker locally, or a
Render/Supabase dev instance) — the `.env`/config pattern already in place
carries the connection string.

## The Project Constitution (schema source of truth)

From `AI_Project_Execution_Engine.md` Section 2, captured verbatim as the
fields to persist (intake fields from Section 1 map into these):

```
Mission · Purpose · Desired outcome · Success criteria · Constraints ·
Assumptions · Non-negotiables · Available resources · Known facts · Unknowns ·
Risks · Decisions · Change history
```

**Two load-bearing rules from the doc that the schema must honor:**
- **Versioned, not editable-in-place.** Every change is an addition to
  `Change history`, never a silent overwrite (Section 2).
- **Per-project namespacing.** One project's state never leaks into another's
  (destination Section 11 "data isolation"; Spec Part XX). Every row is scoped
  by `project_id`.

## Proposed sessions (each a small, tested, committed brick)

Counts are estimates; each is one ~3-hour brick. We build one at a time, test
gate after each, and only mark Level 3 when you verify.

### Session 6 — DB access seam + config (no schema yet)
- **Adds:** `core/memory/` package; a DB connection/session helper reading a
  `DATABASE_URL` via `Settings` (extend `core/config.py`, don't rewrite it);
  `psycopg`/SQLAlchemy dependency added to `requirements.txt`; `infra/` folder
  for migrations/compose.
- **Decision:** log **D009** (Postgres-first).
- **Test gate (L2):** unit test that config reads `DATABASE_URL`; a connection
  test that is **skipped** when no DB is present (so `pytest` stays green with
  no network, matching current discipline).
- **L3 (you):** `docker compose up` a local Postgres (compose file provided) and
  confirm the connection helper connects.
- **Why first:** establishes the seam with zero schema risk; every later session
  builds on it.

### Session 7 — Constitution schema + migration
- **Adds:** the Constitution table(s) and a **migration** (Alembic or a plain
  SQL migration in `infra/`); the change-history and `project_id` scoping baked
  into the schema; `docs/DATABASE.md` (Spec doc 04) started.
- **New contract:** Constitution schema added to `CONTRACTS.md`.
- **Test gate (L2):** migration applies cleanly to a fresh DB in a test
  (or is skipped without a DB); schema shape asserted.
- **L3 (you):** run the migration against your local Postgres; table exists.

### Session 8 — Constitution repository (create / read / update-as-append)
- **Adds:** `core/memory/constitution.py` — a repository class with
  `create(project)`, `get(project_id)`, `append_change(project_id, change)`,
  honoring "versioned, not in-place." Repository pattern so the DB is swappable
  (Part XXII).
- **Test gate (L2):** repository tested against a real transaction on a
  test DB (integration test — the first in the repo, per TESTING.md's plan),
  **skipped** cleanly when no DB is configured. Create→read round-trips; an
  update appends to change history and never overwrites.
- **L3 (you):** from a Python shell or CLI, create and read back a Constitution.

### Session 9 — CLI wiring + persist-across-runs proof
- **Adds:** CLI subcommands — `constitution create`, `constitution show`,
  `constitution amend` — thin over the repository (no logic in the CLI, D003).
- **Test gate (L2):** CLI tests with an injected fake repository (same
  injection discipline as today), no DB needed.
- **L3 (you) — the milestone bar:** create a Constitution in **run #1**, read it
  back in a **separate run #2** — first locally, then the real proof: create it
  against the **Render Postgres**, trigger a **redeploy**, and confirm it's
  still there from your phone-free CLI. This is the Milestone C definition of
  done.

## What you provision for Milestone C (prep checklist)

Do these once, before Session 9's Level-3 (Sessions 6–8 only need the local DB):

- [ ] **Local Postgres** for dev — Docker Desktop + the `infra/compose` file we'll
  add (fastest), enabling the **pgvector** extension now even though C doesn't
  use it (saves a step at E).
- [ ] **Render account** + a **managed Postgres** instance (or Supabase). Copy its
  connection string into your **local** `.env` as `DATABASE_URL` for testing,
  and into **Render's secret manager** for the deployed run — never commit it.
- [ ] Confirm you can trigger a **manual redeploy** on Render (that's the L3 test).

Not needed yet (later milestones): object storage, a second worker process,
Telegram, web-search keys.

## Cost & safety notes

- Sessions 6–8 automated tests remain **$0, no network** (DB-touching tests skip
  without a DB). No model calls in this milestone at all.
- Running cost introduced: a managed Postgres instance (small monthly) and, at
  L3, a Render service to redeploy. No per-token cost — Milestone C does not call
  a model.
- **Deploy-safety (BUILD_PLAN track):** migrations are the risk surface here.
  Every migration is forward-only, reviewed, and run against a fresh/dev DB
  before the deployed one — no destructive operations on existing rows.

## After C

Milestone **D** (Cloud API + Telegram) sits directly on this — the first
phone-reachable version. We break D out the same way once C shows Level 3.

---

**Awaiting approval of this plan.** On your go-ahead I start **Session 6** only
(DB seam + config + D009), build it, test it, and stop for your Level-3 before
Session 7 — one brick at a time, as protocol requires.
