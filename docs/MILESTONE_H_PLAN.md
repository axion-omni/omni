# Milestone H — Single agent, unattended (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> H1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §2 (the scholarship worked example), §8 (agent contract),
> §15/§16; Construction Spec Part V (Stage 6), Part XIV (agent contract).

> **Capability after this milestone:** give one objective and the agent completes
> a real multi-step task unattended — reason, call tools, use memory — and returns
> a structured result. First time it is genuinely useful.

## Definition of done (authoritative gate)
Destination §15 Milestone H: **“The scholarship-research example (§2) completes
end-to-end from the phone.”** Construction Spec Stage 6: “Given ‘compare 3 cloud
DBs’, produces a cited report with no manual step.” Verified L3 from phone.

## Prerequisites
- **Milestones F + G at L3** (workers + tools), **E at L3** (memory for grounding).

## Contracts introduced (add to CONTRACTS.md as built)
- `core/agents/base.py`: `class Agent` with `role`, `run(task, context,
  tools, model_pipeline) -> AgentResult`.
- **Agent contract output** (fixed shape, destination §8): `task`, `work_done`,
  `output`, `evidence` (citations/tool results), `tests_or_checks`,
  `failures`, `assumptions`, `risks`, `next_action`. Persisted per project.
- `core/agents/loop.py`: the reason→act(tool)→observe→repeat loop with a step cap.

## Likely decisions to log (DECISIONS.md)
- **D0xx — the agent contract fields** (frozen shape above) — every agent returns
  exactly this; downstream (verification, orchestrator) depends on it.
- **D0xx — step/tool budget + stop conditions** (avoid runaway loops; cost cap
  via `estimated_cost` from S3).
- **D0xx — labeled facts** (Known/Assumed/Unknown, §4 of the engine doc) carried
  in `evidence`/`assumptions`.

## Sessions

### Session H1 — Agent contract + result model
- **Files:** `core/agents/base.py`, `core/agents/models.py` (`AgentResult`
  Pydantic, the fixed fields); `tests/test_agent_contract.py`.
- **Test gate (L2):** `AgentResult` enforces the required fields; serializes to
  JSON for persistence; empty/missing required fields rejected.
- **Commit:** `feat: Session <n> - agent contract + result model (Milestone H)`.

### Session H2 — Agent reasoning/tool loop
- **Files:** `core/agents/loop.py`; `tests/test_agent_loop.py`.
- **Steps:** drive a model (via the S1–S5 pipeline) that may call tools (G loop),
  read memory (E), and must end by returning an `AgentResult`. Enforce step +
  cost budgets.
- **Test gate (L2):** a scripted fake model does research→tool→answer and yields a
  valid `AgentResult` with evidence; exceeding the step budget stops cleanly with
  a `failures`/`next_action` set; no network.
- **Operator L3:** local: a bounded task returns a cited result.
- **Commit:** `feat: Session <n> - single-agent reason/act loop`.

### Session H3 — Persist agent output + run as a worker job
- **Files:** store `AgentResult` per project (reuse memory/schema, add
  `agent_outputs` migration); job handler `agent_task`; `tests/test_agent_job.py`.
- **Test gate (L2):** an `agent_task` job runs the loop (faked) and persists the
  result; retrieval returns it; delivery to phone faked.
- **Operator L3:** dev: dispatch an agent task; result stored + returned.
- **Commit:** `feat: Session <n> - persisted agent output + agent worker job`.

### Session H4 — The §2 scholarship example, end-to-end from phone
- **Files:** a concrete task config for the scholarship-research example;
  `docs/EXAMPLES.md`; `tests/test_scholarship_example.py` (faked model/tools).
- **Test gate (L2):** the example pipeline produces a structured, cited result
  with the fake providers (proves wiring, not model quality).
- **Operator L3 — THE GATE:** from the phone, run the §2 example → a cited report
  returns with no manual step. Milestone H done.
- **Commit:** `feat: Session <n> - scholarship example end-to-end (Milestone H done)`.

## Security / deploy-safety notes
- Budgets (steps, tools, cost) are hard limits — a runaway agent is a cost/DoS risk.
- Tool-tier enforcement (G) still applies; `dangerous`/`write` await J.
- Untrusted tool/memory content is never treated as instructions.

## Explicitly deferred
- Planning a big objective into a task graph → **Milestone I**. Multiple
  cooperating agents + independent verification → **Milestone K**. Approvals → **J**.
