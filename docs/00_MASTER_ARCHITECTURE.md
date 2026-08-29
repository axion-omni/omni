# Master Architecture — Pointer

The full destination architecture for this project is
**`PERSONAL_AI_OS_MASTER_ARCHITECTURE.md`**, delivered alongside this repo
(not stored inside it, to avoid duplicating a large document that changes
independently of code commits — keep it wherever the rest of the project's
reference documents live, and treat it as authoritative).

This file exists only so anyone opening `docs/` finds the pointer
immediately, per that document's own Section 14 instruction.

## Quick orientation for a new session (human or AI)

1. Read `PERSONAL_AI_OS_MASTER_ARCHITECTURE.md` in full — it is the
   destination, and it explicitly defines its relationship to every other
   document in this project (Section 0).
2. Read `docs/PROJECT_STATE.md` and `docs/progress.json` — current status,
   verification level, next brick.
3. Read `docs/SYSTEM_ARCHITECTURE.md` — what's actually built, as opposed
   to what's planned.
4. Read `docs/DECISIONS.md` — why things are the way they are, especially
   D001–D005, before proposing to change any of them.
5. Read `docs/CONTRACTS.md` — exact interfaces already in place. New code
   must honor these unless a documented decision changes them.
6. Read `docs/ROADMAP.md` — session-level plan for the current milestone.

Do not begin implementation before completing this list. This is the
"Understand → Inspect" step of the standing build protocol
(`PERSONAL_AI_OS_MASTER_ARCHITECTURE.md`, Section 0) — it is not optional
and it is not satisfied by skimming.
