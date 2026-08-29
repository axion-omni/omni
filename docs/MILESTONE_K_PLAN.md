# Milestone K — Multi-agent + verification separation (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> K1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §6 (orchestrator mediates), §8 (creator ≠ verifier), §15/§16;
> Construction Spec Stages 11 & 13; `AI_Project_Execution_Engine.md` §11,§14,§15.

> **Capability after this milestone:** 2–3 specialized agents cooperate through
> the orchestrator (Researcher → Developer handoff, no manual copy-paste), and a
> separate verifier catches a deliberately broken output before it’s “done”.

## Definition of done (authoritative gate)
Destination §15 Milestone K: **“Creator/verifier separation demonstrably catches
a deliberately broken output.”** Construction Spec Stage 11 (“Researcher→Developer
handoff with no manual copy-paste”) + Stage 13 (“a deliberately-broken output is
caught by the verifier”). Verified L3.

## Prerequisites
- **Milestone I at L3** (orchestrator + task graph) and **J at L3** (gates).

## Contracts introduced (add to CONTRACTS.md as built)
- Agent roles under `core/agents/roles/`: e.g. `researcher.py`, `developer.py`,
  `verifier.py`, `critic.py` — each an `Agent` (H contract), differing by role
  prompt + allowed tools.
- **Verification rule (structural):** the orchestrator assigns a task’s verifier
  to an agent instance **different from its creator**; a task is not `done` until
  a verifier returns pass. Encoded in `core/orchestrator.py` dispatch.
- Handoff via the task graph + persisted `AgentResult` (no direct agent→agent
  calls; the orchestrator passes prior outputs as context).

## Likely decisions to log (DECISIONS.md)
- **D0xx — creator ≠ verifier enforced in dispatch** (identity check), not by
  convention.
- **D0xx — the Adversarial/Critic role** produces “evidence against the
  assumption”, feeding §16 acceptance criterion #5.
- **D0xx — verification outcome schema** (pass/fail + reasons) and how a fail
  re-opens the task (bounded retries, then escalate to a phone approval).

## Sessions

### Session K1 — Role library on the H agent base
- **Files:** `core/agents/roles/{researcher,developer,verifier,critic}.py`;
  `tests/test_agent_roles.py`.
- **Test gate (L2):** each role builds its distinct role prompt + tool allowlist;
  all return the H `AgentResult` contract; faked models, no network.
- **Commit:** `feat: Session <n> - specialized agent roles (Milestone K)`.

### Session K2 — Orchestrated handoff (Researcher → Developer)
- **Files:** orchestrator passes a completed task’s `AgentResult` as context to a
  dependent task’s agent; `tests/test_handoff.py`.
- **Test gate (L2):** a 2-task graph runs Researcher then Developer; the
  Developer receives the Researcher’s output as context (asserted), with **no
  manual step**; agents faked.
- **Operator L3:** dev: a research→build task chain completes with context flowing.
- **Commit:** `feat: Session <n> - orchestrated researcher→developer handoff`.

### Session K3 — Independent verification (creator ≠ verifier)
- **Files:** dispatch assigns a different agent as verifier; task not `done`
  until verify passes; `tests/test_verification.py`.
- **Test gate (L2):** a task whose creator returns a **deliberately broken**
  output is failed by the verifier (not marked done); a correct output passes;
  the verifier is provably a different instance than the creator.
- **Operator L3:** dev: inject a broken output → verification catches it.
- **Commit:** `feat: Session <n> - creator≠verifier verification gate`.

### Session K4 — Critic/adversarial pass + end-to-end
- **Files:** critic role wired to challenge a key assumption; `tests/test_critic.py`.
- **Test gate (L2):** on a task with a shaky assumption, the critic returns
  “evidence against”, recorded in the result (feeds §16 #5); faked model.
- **Operator L3 — THE GATE:** on a real task, observe (a) the handoff with no
  copy-paste and (b) a deliberately broken output caught by the verifier.
  Milestone K done.
- **Commit:** `feat: Session <n> - adversarial critic + verification e2e (Milestone K done)`.

## Security / deploy-safety notes
- Verification separation is **structural** (different agent instance), enforced
  server-side — the core anti-“confidently wrong” control.
- Bounded re-open loops on failed verification (avoid infinite retries/cost).
- All agents still bound by tool tiers (G) and approval gates (J).

## Explicitly deferred
- Large agent swarms / dynamic role creation → post-MVP. Self-improvement of
  workflows → post-MVP (Stage 17, human-approved only).
