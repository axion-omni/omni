# Project State

Machine-readable state: `docs/progress.json` (kept in sync with this file).

## Overall
- **Current milestone:** Milestone 1 — "can communicate with models" — Session 3 of 5 built (Level 2)
- **Current stage:** Stage 2 — Model abstraction & routing (registry done; routing/retry next)
- **Current brick:** Session 3 (model registry) built, Level 2 → Session 4 (routing table) next
- **Build protocol:** non-negotiable build protocol in effect.

## Completed
- Session 1 — Model abstraction + Anthropic provider (level 3 verified)
- Session 1b — OpenRouter provider + minimal factory (level 3 verified, D004)
- Session 2 — CLI entrypoint (`apps/cli/main.py`) — level 2 (operator L3 pending)
- Session 3 — Model registry (`core/models/registry.py`): logical names
  (`reasoning-strong`/`coding`/`cheap-fast`) → `(provider, model_id)`;
  provider-sourced capabilities; pure `estimated_cost()`;
  `ModelNotRegisteredError`; CLI gained `--model <logical-name>`; factory
  reused as the registry's construction primitive (D007). Level 2.
- 31 unit tests total, all passing (level 2 — assistant sandbox)
- CLI → registry → factory → provider chain confirmed wired end-to-end with
  injected fakes, plus a real (non-injected) script run that builds the
  registry and fails cleanly with no key — still not run with a real key by
  the operator.

## In progress
- Verification level 3 pending for Session 2 (CLI with a real key) and
  Session 3 (`pytest -v` + `python apps/cli/main.py "say hello" --model
  reasoning-strong` with a real key) — operator has not yet run either.

## Blocked
- None.

## Decisions pending
- None new since D007.

## Next
- Operator: run `pytest -v` (expect 31 passed) and
  `python apps/cli/main.py "say hello" --model reasoning-strong` with a real
  key (Anthropic or OpenRouter, whichever ACTIVE_PROVIDER points at) to
  confirm Session 3 at level 3 (this also covers Session 2's pending L3).
- Then: Session 4 — Routing table + MODEL_POLICY (task type + policy →
  logical name), per ROADMAP.md / BUILD_PLAN.md / Master Construction Spec
  Part VII, Session 4.

## Last verified
Level 3 confirmed for Sessions 1 and 1b. Sessions 2 and 3: level 2 only so far.
