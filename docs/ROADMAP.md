# Roadmap

Full detail lives in the companion `00_MASTER_CONSTRUCTION_SPECIFICATION.md`
(Parts VI–VIII). This file is the short, repo-local version — update it as
stages complete so it never drifts far from that source document.

## Milestones

| # | Milestone | Status |
|---|---|---|
| 1 | Can communicate with models | **In progress** — Session 1 of 5 done |
| 2 | Has persistent project memory | Not started |
| 3 | Can retrieve knowledge (RAG) | Not started |
| 4 | Can use tools | Not started |
| 5 | Can execute a task unattended | Not started |
| 6 | Can build and test software | Not started |
| 7 | Can plan a project | Not started |
| 8 | Can orchestrate workers | Not started |
| 9 | Can autonomously execute bounded projects | Not started |
| 10 | General project execution platform | Not started |

## Milestone 1 sessions (Stages 0–2)

| Session | Deliverable | Status |
|---|---|---|
| 1 | Model abstraction + Anthropic provider | ✅ Done — commit `c9925a1` |
| 2 | CLI entrypoint + config hardening | ✅ Done |
| 3 | Model registry (logical names → provider+model) | ⏳ Built, Level 2 — operator L3 pending |
| 4 | Routing table + MODEL_POLICY | ⏳ Built, Level 2 — operator L3 pending |
| 5 | Retry + fallback logic | ⏳ Built, Level 2 — operator L3 pending |

Sessions 3–5 complete construction-spec **Milestone 1** (Stages 0–2, "can
communicate with models") at Level 2 — pending the operator's Level-3 run.

**Milestone 2 (Stage 3) — persistent project state on Postgres** (see
`MILESTONE_C_PLAN.md` for the session breakdown):

| Session | Deliverable | Status |
| 6 | DB access seam + config (D009, Postgres-first) | ✅ Done, Level 3 — commit `bdf9100` |
| 7 | Constitution schema + migration (D010) | ✅ Done, Level 3 — commit `a787441` |
| 8 | Constitution repository (create/read/append) | ✅ Done, Level 3 — commit `8610b57` |
| 9 | CLI wiring + persist-across-redeploy proof | NEXT |

Deterministic build specs for Milestones D–L live in `docs/MILESTONE_*_PLAN.md`
(indexed by `docs/BUILD_INSTRUCTIONS_INDEX.md`).

Sessions 6+ (Stage 3 onward) get broken out here as Milestone 1 completes —
see the Master Construction Specification's own note on why they're not
pre-specified in full daily-session detail yet.
