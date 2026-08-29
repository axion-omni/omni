# Milestone J — Approval gates, live on Telegram (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> J1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §12 (approval gates), §11, §15/§16; Construction Spec Stage 14,
> `AI_Project_Execution_Engine.md` §7 & §17.

> **Capability after this milestone:** a task marked `approval_required` blocks,
> asks you on Telegram (inline Approve/Reject buttons), and resumes only after you
> tap — and the pending state survives a worker restart.

## Definition of done (authoritative gate)
Destination §15 Milestone J: **“An `approval_required` action blocks and resumes
correctly via phone buttons.”** Construction Spec Stage 14: “An ‘approval
required’ action provably blocks until you respond.” Verified L3 from phone.

## Prerequisites
- **Milestones F + I at L3** (workers + orchestrator/task graph; approvals gate
  dispatch). D at L3 (Telegram) for the buttons.

## Contracts introduced (add to CONTRACTS.md as built)
- Migration `00xx_approvals.sql`: `approvals(id, project_id, task_id, prompt,
  status [pending|approved|rejected], decided_at, decided_by)`, per-project.
- `core/approvals.py`: `request_approval(task, settings) -> approval_id` (creates
  pending row + sends a Telegram message with inline buttons),
  `resolve(approval_id, decision, user_id)`.
- Telegram callback handling: `POST /telegram/webhook` also parses
  `callback_query` (button taps); auth by the same allowlist.

## Likely decisions to log (DECISIONS.md)
- **D0xx — orchestrator refuses to dispatch a task while its approval is
  pending** (the gate is enforced at dispatch, server-side).
- **D0xx — approval identity**: only allowlisted users can decide; the decision
  records `decided_by`.
- **D0xx — timeout policy** for un-answered approvals (default: stay pending).

## Sessions

### Session J1 — Approvals schema + repository
- **Files:** `infra/migrations/00xx_approvals.sql`, `core/approvals.py` (create/
  read/resolve); `tests/test_approvals.py`.
- **Test gate (L2):** create a pending approval; resolve to approved/rejected;
  an already-decided approval can’t be re-decided; per-project scoped; fake store.
- **Operator L3:** migrate; create + resolve a row on dev DB.
- **Commit:** `feat: Session <n> - approvals schema + repository (Milestone J)`.

### Session J2 — Orchestrator honors the gate
- **Files:** orchestrator change: a task with `approval_required` and no
  approved approval is **not dispatched**; it requests approval and parks;
  `tests/test_orchestrator_approval.py`.
- **Test gate (L2):** a gated task blocks (never dispatched) until an approval row
  is approved; then it dispatches; a rejected approval marks the task
  rejected/skipped and unblocks the graph appropriately.
- **Operator L3:** dev: a gated task stays blocked until approved.
- **Commit:** `feat: Session <n> - orchestrator enforces approval gate`.

### Session J3 — Telegram inline buttons + callback handling
- **Files:** send approval prompts with inline keyboard; parse `callback_query`
  in the webhook → `resolve`; `tests/test_telegram_callbacks.py`.
- **Test gate (L2):** an approval request builds the correct inline-keyboard
  payload (faked send); a callback from an allowlisted user resolves the approval;
  a callback from a non-allowlisted user is ignored.
- **Operator L3:** none yet (J4).
- **Commit:** `feat: Session <n> - Telegram approval buttons + callbacks`.

### Session J4 — Restart-survival + end-to-end from phone
- **Files:** ensure pending approvals + parked tasks are re-loaded from the DB on
  restart (orchestrator/worker are stateless over Postgres); `tests/test_approval_resume.py`.
- **Test gate (L2):** with a pending approval persisted, simulate restart → the
  gate is still enforced and resolvable; resolving resumes the task.
- **Operator L3 — THE GATE:** from the phone, a gated action prompts with
  buttons; restart the worker; tap Approve → the task resumes; tap Reject →
  it doesn’t. Milestone J done.
- **Commit:** `feat: Session <n> - approval gates live on Telegram (Milestone J done)`.

## Security / deploy-safety notes
- Only allowlisted users can approve; record `decided_by` (audit).
- The gate is enforced **server-side at dispatch**, never by trusting the agent.
- Pending state lives in Postgres → survives restarts/redeploys (§16 guarantee).

## Explicitly deferred
- Rich approval UIs / “more info” dialogs → post-MVP. Multi-approver policies → post-MVP.
