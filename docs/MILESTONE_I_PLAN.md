# Milestone I — Planner + task graph + Orchestrator (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> I1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §6 (orchestrator), §8, §15; Construction Spec Stages 8–10, Part
> VIII (decomposition), and `AI_Project_Execution_Engine.md` §1–§12.

> **Capability after this milestone:** a one-paragraph objective becomes a
> Constitution + a **task graph**, and the Orchestrator runs it in the right
> order (parallel where independent, blocked where dependent) via workers.

## Definition of done (authoritative gate)
Destination §15 Milestone I: **“A one-paragraph objective becomes a task graph;
a multi-step task runs with correct sequencing.”** Construction Spec Stages 8–10:
a task list a human recognizes; parallel vs blocked identifiable; correct
sequencing. Verified L3 from phone.

## Prerequisites
- **Milestones C + H at L3** (state + a working single agent to dispatch to).

## Contracts introduced (add to CONTRACTS.md as built)
- `core/planning/intake.py`: `objective -> Constitution` draft + triaged
  questions (Critical/Important/Useful/Optional, engine §3). Ask only ≥Important;
  default the rest explicitly.
- `core/planning/graph.py`: `Task`(id, description, deps, agent_role, status,
  approval_required) + `TaskGraph` (build, `ready_tasks()`, `mark_done`), persisted
  (migration `00xx_task_graph.sql`, per-project).
- `core/orchestrator.py`: `next_actions(graph)` (what can run now, respecting
  deps), `dispatch(task)` → enqueues an agent job (F). **Agents never call each
  other**; only the orchestrator dispatches (destination §6).

## Likely decisions to log (DECISIONS.md)
- **D0xx — task graph representation** (adjacency in Postgres; cycle detection).
- **D0xx — intake question triage thresholds** and defaulting policy.
- **D0xx — orchestrator is stateless over the DB** (re-derives ready set each
  tick) so it survives restarts.

## Sessions

### Session I1 — Objective → Constitution draft + question triage
- **Files:** `core/planning/intake.py`; `tests/test_intake.py`.
- **Test gate (L2):** a fake model turns a paragraph into a `Constitution` with
  labeled knowns/unknowns and a triaged question list; only ≥Important are marked
  “ask”; no network.
- **Operator L3:** a real paragraph yields a sane draft + a short question set.
- **Commit:** `feat: Session <n> - objective intake + question triage (Milestone I)`.

### Session I2 — Task graph model + persistence
- **Files:** `core/planning/graph.py`, migration `00xx_task_graph.sql`;
  `tests/test_task_graph.py`.
- **Test gate (L2):** build a graph; `ready_tasks()` returns only dep-satisfied
  tasks; cycle detection raises; independent tasks both ready (parallelism
  visible); persistence round-trips via a fake store.
- **Operator L3:** migrate; persist + reload a graph on dev DB.
- **Commit:** `feat: Session <n> - task graph model + schema`.

### Session I3 — Decompose spec → task graph
- **Files:** `core/planning/decompose.py` (Constitution/spec → tasks + deps);
  `tests/test_decompose.py`.
- **Test gate (L2):** a fake planner model produces a graph a human recognizes as
  reasonable for a sample objective; deps consistent (no dangling/cyclic).
- **Operator L3:** a real objective → a plausible graph.
- **Commit:** `feat: Session <n> - decomposition into a task graph`.

### Session I4 — Orchestrator dispatch (correct sequencing)
- **Files:** `core/orchestrator.py`; a job handler that advances the graph;
  `tests/test_orchestrator.py`.
- **Test gate (L2):** given a fixed graph, the orchestrator dispatches only ready
  tasks, waits on blocked ones, and completes in a correct topological order
  (agents faked); a failed task blocks its dependents, not the whole graph.
- **Operator L3 — THE GATE:** from the phone, a paragraph objective → task graph
  → a multi-step run completes in the right order. Milestone I done.
- **Commit:** `feat: Session <n> - orchestrator dispatch + sequencing (Milestone I done)`.

## Security / deploy-safety notes
- Orchestrator re-derives state from the DB each tick → restart-safe (ties into F).
- Cost budget per objective (sum `estimated_cost`); stop + report if exceeded.
- No agent-to-agent dispatch; the orchestrator is the only scheduler.

## Explicitly deferred
- `approval_required` tasks actually pausing for phone approval → **Milestone J**.
- Multiple cooperating roles + adversarial verification → **Milestone K**.
- Continuous replanning on new findings → post-MVP (Stage 20 idea).
