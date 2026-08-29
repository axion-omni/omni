# Milestone F — Job queue + background workers (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> F1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §13 (Cloud API never blocks; workers), §14 (deploy: separate
> worker process), §16 (crash-resume acceptance); Construction Spec Part XII.

> **Capability after this milestone:** dispatch a long task from the phone, close
> the app, and get the result later. The Cloud API stops doing work inline (fixes
> Milestone D’s synchronous limitation, D013) and hands tasks to workers.

## Definition of done (authoritative gate)
Destination §15 Milestone F: **“A task dispatched from the phone completes after
the phone app is closed and reopened.”** Plus §16: **killing a worker mid-task
leaves a resumable state, never a silent loss.** Verified L3 from phone.

## Prerequisites
- **Milestones C + D at L3** (Postgres + phone path).
- **Operator prep:** a second Render service (Background Worker) running the
  worker command, sharing the same `DATABASE_URL`.

## New dependencies / config / secrets
- None required beyond Postgres (queue is a Postgres table + `SELECT … FOR UPDATE
  SKIP LOCKED`). Config: `WORKER_POLL_SECONDS`, `JOB_MAX_ATTEMPTS`.

## Contracts introduced (add to CONTRACTS.md as built)
- Migration `0003_jobs.sql`: `jobs(id, project_id, type, payload jsonb, status
  [queued|running|done|failed], attempts, checkpoint jsonb, result jsonb,
  created_at, updated_at)`, per-project scoped.
- `core/jobs/queue.py`: `enqueue(project_id, type, payload, settings) -> job_id`,
  `claim_next(settings) -> Job|None` (atomic), `checkpoint(job_id, data)`,
  `complete(job_id, result)`, `fail(job_id, error)`.
- `workers/run.py`: the worker loop entrypoint (a process, not a request).

## Likely decisions to log (DECISIONS.md)
- **D0xx — queue = Postgres (`FOR UPDATE SKIP LOCKED`)**, not Redis/Celery: one
  fewer moving part; matches “managed Postgres is the backbone” (§7/§14).
- **D0xx — job handler registry**: `type -> handler(payload, checkpoint)`.
- **D0xx — checkpointing contract**: handlers persist progress so a killed worker
  resumes from the last checkpoint (the §16 crash-resume guarantee).

## Sessions

### Session F1 — Jobs schema + queue repository
- **Files:** `infra/migrations/0003_jobs.sql`; `core/jobs/queue.py`;
  `tests/test_queue.py`.
- **Test gate (L2):** enqueue/claim/complete/fail modeled against an injected
  fake store; state transitions correct; `claim_next` returns None when empty.
- **Operator L3:** migrate; enqueue + claim a row on the dev DB.
- **Commit:** `feat: Session <n> - Postgres job queue (Milestone F)`.

### Session F2 — Worker loop + handler registry
- **Files:** `workers/__init__.py`, `workers/run.py`, `core/jobs/handlers.py`
  (`register(type)` decorator); `tests/test_worker.py`.
- **Steps:** loop = claim → dispatch to handler → checkpoint → complete/fail with
  attempt cap. Sleep injectable (like retry.py) so tests don’t wait.
- **Test gate (L2):** a fake job runs its handler and is marked done; a handler
  raising is retried up to `JOB_MAX_ATTEMPTS` then failed; loop uses injected
  claim/sleep — no DB.
- **Operator L3:** run `python workers/run.py` against dev DB; a queued job runs.
- **Commit:** `feat: Session <n> - background worker loop + handler registry`.

### Session F3 — Crash-resume (checkpointing)
- **Files:** checkpoint read/write in the loop; a sample multi-step handler;
  `tests/test_worker_resume.py`.
- **Test gate (L2):** simulate a crash mid-handler (raise after checkpoint N);
  re-claim resumes from checkpoint N, not from scratch; no duplicated side effects.
- **Operator L3:** start a long job, `kill` the worker, restart → it resumes.
- **Commit:** `feat: Session <n> - worker checkpoint + resume`.

### Session F4 — Cloud API dispatches instead of blocking + phone notify
- **Files:** webhook now `enqueue`s and immediately acks (“working on it…”);
  worker sends the result to Telegram on completion (reuse `send_message`);
  `tests/test_api_webhook.py` updated.
- **Steps:** removes D013’s synchronous limitation. The API returns fast; the
  worker delivers the answer asynchronously.
- **Test gate (L2):** an authorized update enqueues a job and acks; a completed
  job triggers a `send_message` (both faked).
- **Operator L3 — THE GATE:** from the phone, dispatch a task, close the app,
  reopen later → the result arrived. Milestone F done.
- **Commit:** `feat: Session <n> - async dispatch + phone delivery (Milestone F done)`.

## Security / deploy-safety notes
- Jobs are **per-project scoped**; a worker only acts within a job’s project.
- Idempotency: completing/among retries must not double-apply side effects.
- The worker is a **separate Render service**; deploy both from the same image.

## Explicitly deferred
- What the jobs actually *do* beyond a model call → tools (G), agents (H).
- Approvals mid-job → **Milestone J** (a job can park in `awaiting_approval`).
