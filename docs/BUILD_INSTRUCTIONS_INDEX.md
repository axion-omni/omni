# Build Instructions Index — how to finish this project without guessing

This file is the entry point for **any agent or person** continuing the build,
especially in a fresh session with no memory of prior context. Read it first.

## Read order (every session, before touching code)
1. `docs/00_MASTER_ARCHITECTURE.md` (pointer) → `PERSONAL_AI_OS_MASTER_ARCHITECTURE.md`
   (destination; **governs on any conflict**, per D006).
2. `docs/PROJECT_STATE.md` + `docs/progress.json` — exactly where things stand
   (the **source of truth for status**; these win over any plan doc).
3. `docs/SYSTEM_ARCHITECTURE.md` — what is actually built vs planned.
4. `docs/DECISIONS.md` — why things are the way they are (D001–D010+). Don't
   redesign a decision without a stated reason + a new decision entry.
5. `docs/CONTRACTS.md` — exact interfaces in place. **Honor them; code wins.**
6. `docs/BUILD_PLAN.md` — the milestone route (A–L) and per-milestone gates.
7. The milestone plan for the current milestone (below).

## The non-negotiable protocol (applies to every brick)
Understand → Inspect → Plan → Implement → Test → Integrate → Verify →
Document → Commit. Bricks are **small, single-purpose, tested, integrated,
documented in the six standing docs, and committed** with a real git commit.

**Verification levels:** 1 generated (≈nothing) · 2 tested in the build
environment (green, no network/keys unless noted) · 3 verified by the operator
on their machine/deployment (from Milestone C on: **verified from the phone
against the deployed instance**). Never mark anything above Level 2 in
PROJECT_STATE.md without the operator confirming Level 3. **A milestone does not
start until its dependencies show Level 3.**

**Test discipline:** the automated suite must stay green with **no network and
no real keys** — inject fakes (providers, DB connector, http, sleep) exactly as
the existing tests do. Live checks (DB, model, phone) are Level-3 and must SKIP
when their env var/credential is absent.

**Commit hygiene:** stage only the brick's files + the six standing docs +
`progress.json`; **never commit** the untracked companion reference docs
(`00_MASTER_CONSTRUCTION_SPECIFICATION-1.md`, `AI_Project_Execution_Engine.md`,
`AI_Mastery_Learning_Roadmap.md`, the `.docx` files). Commit author has been
`AI Execution Engine <builder@local>` (pass inline with `git -c` if unset).
Follow the repo pattern: one `feat:` commit, then a tiny `record … commit hash
in progress.json` follow-up.

## Milestone plans (deterministic build specs)
Each file lists: definition of done (authoritative gate), prerequisites +
operator prep, new deps/config/secrets, contracts introduced, likely decisions,
and **sessions** (each with goal, files, steps, L2 test gate, operator L3,
commit message).

| Milestone | Capability | Plan file | Status |
|---|---|---|---|
| A | Talk to a model (CLI) | (BUILD_PLAN.md) | Done, L2/L3 |
| B | Registry, routing, retry | (BUILD_PLAN.md) | Code-complete L2 |
| C | Persistent state (Postgres) | `MILESTONE_C_PLAN.md` | S6–S7 built L2; S8–S9 left |
| D | **Cloud API + Telegram (phone!)** | `MILESTONE_D_PLAN.md` | Planned |
| E | Memory + RAG (pgvector) | `MILESTONE_E_PLAN.md` | Planned |
| F | Job queue + workers | `MILESTONE_F_PLAN.md` | Planned |
| G | Tools (sandboxed) | `MILESTONE_G_PLAN.md` | Planned |
| H | Single agent (useful!) | `MILESTONE_H_PLAN.md` | Planned |
| I | Planner + task graph + orchestrator | `MILESTONE_I_PLAN.md` | Planned |
| J | Approval gates on Telegram | `MILESTONE_J_PLAN.md` | Planned |
| K | Multi-agent + verification | `MILESTONE_K_PLAN.md` | Planned |
| L | MVP: full loop, phone-only | `MILESTONE_L_PLAN.md` | Planned |

## Two capability thresholds to steer by
- **First phone-usable:** end of **Milestone D**.
- **First genuinely useful (real task unattended):** end of **Milestone H**.
- **MVP (the vision):** **Milestone L** = the 10 checks in `PERSONAL_AI_OS_
  MASTER_ARCHITECTURE.md` §16, verified from the phone.

## How to execute a milestone (recipe)
1. Confirm dependencies are Level 3 in `PROJECT_STATE.md`.
2. Open its `MILESTONE_<X>_PLAN.md`; do the operator prep it lists.
3. For each session in order: implement the files, make its L2 test gate pass,
   update the six docs + `progress.json`, commit; hand the L3 check to the
   operator; only advance after L3 where the gate requires it.
4. If the plan and reality diverge, the **code + CONTRACTS.md win** — update the
   plan file and add a `DECISIONS.md` entry rather than silently improvising.

## Session-number mapping
Global sessions so far: S1, S1b, S2, S3, S3-fix, S4, S5, S6, S7. Milestone plans
use local labels (D1, E2, …); assign each the next free `S<n>` when you build it
and record it in `progress.json`.
