# Milestone L — MVP: full loop, phone-only (Deterministic Build Spec)

> **How to use this file.** L is mostly **integration + verification**, not new
> subsystems. Its gate is the destination's §16 acceptance list, verified from a
> real phone against the deployed system. Labels L1… map to the next global
> `S<n>`. Code + CONTRACTS win. Grounded in: destination §15 (Milestone L) & §16
> (acceptance).

> **Capability after this milestone:** the whole loop works from your phone; the
> PC is only needed to *build*, never to *use*.

## Definition of done (authoritative gate) — the 10 checks (§16)
All true, verified **from an actual phone** against the deployed instance:
1. A phone objective (text/voice) is acknowledged within seconds even if the task takes hours.
2. It asks clarifying questions only when genuinely needed — not an interrogation.
3. A multi-step task completes with the app closed for part of it; progress updates arrive unprompted.
4. An approval-gated action blocks and resumes only after explicit phone approval.
5. The Adversarial/Critic mechanism produces a real "evidence-against-your-assumption" at least once.
6. A deliberately broken agent output is caught by verification before reaching the phone as finished.
7. Killing a worker mid-task never silently loses it — it resumes or reports failure cleanly.
8. "What's the status of X" and "what has this cost so far" answer accurately from the phone.
9. Switching the active provider needs a config/env change only — no code change, no redeploy.
10. None of the above required a terminal or the PC.

## Prerequisites
- **Milestones A–K all at Level 3.** L does not start until they are.
- Operator prep: staging + production Render services; object storage if any
  artifacts are surfaced; scheduled DB backups.

## Sessions

### Session L1 — Status + cost queries from the phone (check #8)
- **Files:** `core/reporting.py` (`project_status(project_id)`,
  `cost_to_date(project_id)` — sum persisted `estimated_cost` per model call,
  sourced from the event/job records); Telegram commands `/status`, `/cost`;
  `tests/test_reporting.py`.
- **Test gate (L2):** status summarizes task-graph state; cost sums recorded
  per-call costs (fake data); per-project scoped.
- **Operator L3:** ask from phone → accurate status + cost.
- **Commit:** `feat: Session <n> - phone status + cost reporting (Milestone L)`.

### Session L2 — Progress updates + fast ack (checks #1, #3)
- **Files:** unprompted progress messages from the worker at task boundaries;
  the API acks within seconds (already async since F); `tests/test_progress.py`.
- **Test gate (L2):** completing a task emits a progress `send_message` (faked);
  dispatch acks immediately.
- **Operator L3:** long task → immediate ack + progress pings while app closed.
- **Commit:** `feat: Session <n> - unprompted progress updates`.

### Session L3 — Provider switch with no code change (check #9)
- **Files:** none new expected — this is a **verification** brick that
  `ACTIVE_PROVIDER`/`MODEL_POLICY`/registry (S3–S5) already satisfy end-to-end
  through the deployed stack; add `tests/test_provider_switch_e2e.py` if a gap.
- **Operator L3:** change the env var in Render → next task uses the other
  provider, no redeploy of code.
- **Commit:** `test: Session <n> - prove provider switch is config-only`.

### Session L4 — Full acceptance sweep + hardening (all 10)
- **Files:** `docs/ACCEPTANCE.md` (the 10 checks as a runnable operator
  checklist with exact phone steps); fix any gaps found; ensure §16 #5/#6/#7
  (critic, verification, crash-resume) are demonstrable on a real task.
- **Test gate (L2):** full suite green; each of the 10 checks has either an
  automated proxy test or a documented phone procedure.
- **Operator L3 — THE GATE:** walk the 10-item `ACCEPTANCE.md` from your phone;
  all pass. **MVP done.**
- **Commit:** `feat: Session <n> - MVP acceptance sweep (Milestone L done)`.

## Security / deploy-safety notes
- Staging → production with the production deploy behind approval (Stage 15 idea).
- DB backups verified; secrets only in the host manager; least-privilege keys.
- A final security pass: allowlist enforced everywhere, tool tiers + approvals
  active, tool/memory content treated as untrusted.

## After L (genuine extensions, not gaps — §16)
Browser/computer tools (Stage 12), deploy automation with staging-auto/prod-
approval (Stage 15), observability dashboards (Stage 16), self-improving
workflows (Stage 17, human-approved only; no self-replication — Part XXI),
the general non-software execution loop (Stage 18), and further interfaces
(web dashboard, native app, full voice). Each gets its own MILESTONE/plan doc
when reached.
