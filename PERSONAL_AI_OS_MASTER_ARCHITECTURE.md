# The Personal AI Operating System
### Master Destination Architecture & Construction Roadmap

**Document status: this is the destination specification.** It governs every future implementation session. Do not treat anything below as already built unless the "Current Implementation State" section explicitly says so. This document does not implement milestones — it defines what they build toward. Read it fully before writing any code.

**Handoff note:** this project moves to a Claude Opus 5 agent from here. Everything needed to continue without conversation history is either in this document or in the repository's `docs/` folder (delivered alongside this file as a zip). Read both before the first session.

---

## 0. Relationship to Existing Project Artifacts

This project already has documents. Do not ignore, duplicate, or silently contradict them — here's how everything fits together:

| Document | Role | Status |
|---|---|---|
| **This document** | The destination — full end-state architecture (phone-first, cloud-first Personal AI OS) | Governing, effective now |
| `AI_Project_Execution_Engine.md` | An earlier, narrower destination doc (project-execution loop only, no phone/cloud layer) | **Superseded** by this document — its content is absorbed into Sections 4–11 below, not deleted, but this document takes precedence on any conflict |
| `00_MASTER_CONSTRUCTION_SPECIFICATION.md` | Construction philosophy + Stage/Session breakdown for the execution-engine core | **Still valid** for the layers it covers (model abstraction, memory, agents, tools) — its Stage 0–2 work is exactly what's already built (see Section 15) |
| `docs/SYSTEM_ARCHITECTURE.md` (in repo) | As-built architecture, updated every session | **Still the source of truth for "what currently exists in code."** Read this before writing anything. |
| `docs/PROJECT_STATE.md`, `progress.json` | Current brick, verification level, blockers | **Read first, every session**, per the standing build protocol below |
| `docs/DECISIONS.md`, `docs/CONTRACTS.md`, `docs/ROADMAP.md`, `docs/TESTING.md` | Decision log, interfaces, session plan, test strategy | Unchanged in role — this document's milestone sequence (Section 15) extends `ROADMAP.md`, it doesn't replace the sessions already completed there |

**The standing build protocol from prior sessions still applies, unchanged:**

```
Understand → Inspect → Plan → Implement → Test → Integrate → Verify → Document → Commit
```

- Docs are the source of truth, not conversation memory.
- Before significant code: understand existing architecture, inspect relevant files, explain what will be created/modified and why, identify conflicts, then implement.
- Never sacrifice architectural integrity to finish a session. Never redesign working components without a stated reason.
- Every brick: functional, tested, integrated, documented, committed.
- If a requirement conflicts with existing architecture: **stop and say so.** Do not silently invent a solution.
- Verification has three levels — generated (worth ~nothing), tested in the agent's own environment (better), verified by the human on their own machine/deployment (the only level that counts as done). Never mark a brick complete in `PROJECT_STATE.md` above level 2 without the human confirming level 3.

---

## 1. System Overview

A general-purpose personal AI operating system, reachable primarily from a phone, that takes an objective (not a detailed prompt) and researches, plans, delegates, executes, verifies, and reports — asking for human judgment only where it's actually required, and running continuously in the cloud independent of whether the operator's PC or phone app is open at any given moment.

The system is not a chatbot with a phone wrapper. It is the Project Execution Engine (memory, planning, agents, tools, verification — see Sections 7–10) sitting behind a persistent cloud service, reachable through a conversational interface, with the terminal demoted to a development and administration tool rather than the primary runtime.

---

## 2. End-State User Experience

Three worked examples, as the actual bar for "done" (Section 16 turns these into acceptance tests):

> **"Find the best scholarships I can apply for this month, research the requirements, rank them, and prepare the strongest applications. Ask me for anything you need."**
> → System researches (Researcher agent, web tools), ranks with stated reasoning, asks 2–3 high-value questions (not twenty), drafts applications, sends a progress update mid-task, and delivers a ranked report with drafts attached — all from a phone, no terminal touched.

> **"Investigate this market and tell me whether we should enter it. Don't agree with me just because I suggested it."**
> → System produces evidence, opposing evidence, named uncertainties, and a recommendation — explicitly not a decision. The Adversarial Worker role (already specified in the execution-engine architecture) is what makes "don't just agree with me" structurally true rather than a personality instruction that erodes over a long context.

> **"Fix the remaining routing problems in the school SaaS, test everything, and give me a report. Do not deploy without my approval."**
> → Developer agent fixes, Tester agent verifies independently (creator ≠ verifier, already a standing rule), report delivered to phone, production deploy sits at an approval gate until an explicit tap.

**What "feels like one intelligence" requires, concretely:** a single conversational thread per project that persists across days, a system that remembers what it already asked and decided (no re-litigating), and responses that read as one voice even when a research agent, a coding agent, and a critic model produced different parts of the answer.

---

## 3. Target Architecture

```
PHONE / USER INTERFACE
        │  (Telegram first; web dashboard, native app, voice — later, pluggable)
        ▼
MESSAGE + VOICE INTERFACE
        │  (webhook receiver, voice transcription)
        ▼
SECURE CLOUD API
        │  (auth, request validation, rate limiting)
        ▼
ORCHESTRATOR / PERSONAL AI CORE
        │  (what runs next — the same Orchestrator concept already specified,
        │   now long-running and cloud-resident instead of a local process)
        ▼
MEMORY + PROJECT STATE          ◄───┐
        │                           │ (read/write throughout, not a
        ▼                           │  one-way pipe)
PLANNER / TASK DECOMPOSER           │
        │                           │
        ▼                           │
MODEL ROUTER                        │
        │                           │
        ▼                           │
SPECIALIZED AGENTS ──────────────────┘
        │
        ▼
TOOLS / APIs / BROWSER / CODE EXECUTION / DATABASES
        │
        ▼
VERIFICATION + OBSERVABILITY
        │
        ▼
RESULT / ACTION / HUMAN APPROVAL
        │
        ▼
PHONE
```

**The one architectural rule every layer above must respect:** the core (Orchestrator through Verification) never imports anything from an interface layer. Telegram, a future web dashboard, and the CLI are all equally thin clients of the same headless API — this was already decided as D003 in the existing decision log, before any interface but the CLI existed. This document extends that rule to the cloud: the Telegram bot is not special-cased inside the core, it's a client, exactly like the CLI is.

---

## 4. Components

| Component | Responsibility | Talks to |
|---|---|---|
| **Telegram Bot** | Receive text/voice, send responses/approvals/progress | Cloud API only, via webhook |
| **Voice transcription** | Voice note → text before it reaches the API | Telegram Bot (inbound only) |
| **Cloud API (FastAPI)** | Auth, validation, routes requests to the Orchestrator, exposes status/approval endpoints | Every interface; Orchestrator |
| **Orchestrator** | Decides what runs next, dispatches to agents, tracks task graph state | Memory, Planner, Agents, Model Router |
| **Memory + Project State** | Project Constitution, decisions, research, task graph, artifacts — persistent, queryable | Orchestrator, Planner, Agents (read); nothing writes except through the Orchestrator's dispatch |
| **Planner / Task Decomposer** | Objective → questions → spec → task graph | Memory (read/write), Orchestrator |
| **Model Router** | Logical model name + policy → actual provider/model | Every agent, via the same `ModelProvider` interface already built |
| **Specialized Agents** | Research, develop, test, critique, etc. — narrow roles, explicit contracts | Model Router, Tools, Memory |
| **Tool System** | Standardized interface to web search, filesystem, browser, code execution, external APIs | Agents (called), external services (execute against) |
| **Verification layer** | Creator ≠ verifier, structurally enforced | Sits between Agents and Integration — not a separate service, a rule enforced in the Orchestrator's dispatch logic |
| **Observability** | Event log, cost tracking, status queries | Every component emits to it; nothing reads from it except status/reporting paths |
| **Job Queue / Background Workers** | Long-running tasks continue when no client is connected | Orchestrator enqueues; workers pull and execute, reporting back through Memory + Observability |
| **Approval Gate** | Blocks dispatch on `approval_required`/`human_only` actions until a response arrives | Orchestrator (blocks), Cloud API (receives the human's response), Telegram Bot (delivers the prompt and the response) |

---

## 5. Interfaces

**Now:** Telegram — chosen because it supports text, voice notes, inline approve/reject buttons, and push notifications for progress updates, with the lowest implementation cost of any option that meets all four needs.

**Architecturally required, not yet built:** web dashboard (task graph visualization, once there's a graph worth visualizing), native mobile app (only if Telegram's constraints become limiting — not assumed necessary), voice-first interaction (beyond voice-note transcription — full voice conversation, later).

**The constraint that makes adding these cheap:** every interface is a thin client against the same Cloud API. Telegram Bot ≈ CLI ≈ future web dashboard in architectural weight — none of them contain business logic, all of them translate their medium's input into an API call and their medium's output from an API response.

---

## 6. Data Flow & Control Flow

**Data flow, one full cycle:**
```
Phone text/voice → Telegram Bot → (transcribe if voice) → Cloud API
  → Orchestrator reads Project State → determines next action
  → dispatches to Planner (if new objective) or an Agent (if continuing)
  → Agent calls Model Router → Provider → response
  → Agent calls Tools as needed → results flow back through the Agent
  → Verification layer checks output (creator ≠ verifier)
  → Result written to Memory + Observability
  → If approval-gated: Orchestrator halts that branch, Cloud API notifies
    Telegram Bot, phone shows an approve/reject prompt
  → If autonomous: result formatted, sent to phone
```

**Control flow — who decides what runs next:** the Orchestrator, and only the Orchestrator. Agents never dispatch other agents directly; they return control (their Contract output — see Section 8) and the Orchestrator decides the next step from the task graph. This is what keeps the system's behavior traceable — every dispatch decision has one place it was made.

---

## 7. Memory Architecture

Unchanged in substance from the existing execution-engine architecture — what changes is that it's now cloud-resident and must survive the operator's phone/PC being off.

| Store | Contents | Tech |
|---|---|---|
| Relational | Project Constitution, decisions, task graph, status, cost records | PostgreSQL |
| Vector | Research findings, past reasoning, retrievable knowledge | pgvector (same Postgres instance — one fewer moving part) |
| Object storage | Artifacts — code, reports, generated files | S3-compatible (Render Disks, Backblaze B2, or equivalent — vendor-replaceable) |

**Context assembly, not context dumping (unchanged principle):** the Project Constitution loads in full every time (it's kept small by design); everything else is retrieved on demand via the vector store, with closed tasks summarized before embedding rather than stored as full transcripts. This matters more, not less, once agents run unattended for hours — an ever-growing raw log would make every subsequent model call slower and more expensive.

---

## 8. Agent Architecture

Same roster and contract shape as previously specified (Researcher, Developer, Tester, Critic, Architect, Security reviewer — added as real tasks need them, not pre-built speculatively). Two additions specific to the cloud/phone destination:

- **Reporting behavior:** every agent's output, once integrated, must be summarizable into a phone-appropriate message (a few sentences plus an optional attached artifact) — not a raw dump of its full contract output. This is a formatting responsibility of the Orchestrator's response-assembly step, not something each agent needs to handle individually.
- **Long-running tolerance:** agents dispatched via the background worker queue must checkpoint their state (what's done, what's next) into Memory frequently enough that a worker crash loses at most one step, not an entire multi-hour task. This is the direct implementation of "recoverable" (Design Principle 10).

Every agent still returns the same fixed contract (task, work performed, output, evidence, tests, failures, assumptions, risks, next action) — nothing about the cloud destination changes that shape.

---

## 9. Model Routing

**Current implementation status (read `docs/CONTRACTS.md` for the exact interfaces):** `ModelProvider` interface, `AnthropicProvider`, `OpenRouterProvider`, and a minimal `factory.get_active_provider()` switch already exist and are tested. The full capability/cost-aware **Model Registry** (originally scoped as Session 3) is not yet built — build it as specified in `00_MASTER_CONSTRUCTION_SPECIFICATION.md` Part V, with one addition: the registry must be queryable by the Orchestrator for cost-to-date, since phone-delivered cost reporting (Section 13) depends on it.

Routing policy (`free`/`cheap`/`balanced`/`quality`/`maximum`) is unchanged in concept — a task type + policy resolves to a logical model name, never a hardcoded provider string, anywhere above the registry.

---

## 10. Tool Architecture

Unchanged interface shape from the existing specification (`Tool` ABC: name, permission tier, input schema, `execute()`). What's new for the cloud destination:

- Tools that touch the outside world (browser, external APIs, code execution) must run in a **sandboxed worker process**, not inline in the API request/response cycle — a browser session or a code execution can take minutes, and the Cloud API must stay responsive to the phone regardless.
- Tool results are logged to Observability with enough detail to answer "what did this tool actually do" without re-running it — this is what makes a failed multi-hour task debuggable instead of a black box.

---

## 11. Security Boundaries & Permissions

Same four-tier model as previously specified — **autonomous / notify / approval required / human only** — now with cloud-specific enforcement points added:

| Concern | Cloud-specific mechanism |
|---|---|
| API keys/secrets | Host platform's secret manager (never `.env` in production — `.env` remains dev-only) |
| Auth to the Cloud API | Telegram user ID allowlist at minimum for a single-operator system; token-based auth if/when a second interface or second user is added |
| Agent permissions | Tool-level tiers, enforced server-side — never trust a client (including the Telegram bot) to enforce a permission, only the Cloud API's dispatch logic |
| Destructive actions | `human_only` tier tools are not reachable by any agent code path, not just gated by a prompt instruction — enforced at the tool registry level |
| Data isolation | Per-project memory namespacing in Postgres (row-level scoping), so one project's retrieval never leaks into another's |
| Audit logs | Every approval-gated action logged with who/what/when/result — queryable from the phone via a status command |
| Webhook security | Telegram webhook endpoint validates the request signature; not just "any POST to this URL is trusted" |

---

## 12. Human Approval Mechanisms

Delivered as inline Telegram buttons (Approve / Reject / More info) for `approval_required` actions, and as a plain notification (no gate) for `notify` tier. The Orchestrator halts the relevant task-graph branch on dispatch to an approval-gated action, writes a pending-approval record to Memory, and resumes only when the Cloud API receives a matching response. A pending approval survives a worker restart — it's a row in Postgres, not in-process state.

**The design principle this exists to protect (Design Principle 7):** the system researches, challenges assumptions, states uncertainty, and recommends. It does not manufacture certainty to close a task. The Adversarial Worker role and the approval-gate mechanism are the two structural features that make this true regardless of how a session's prompting drifts.

---

## 13. Asynchronous Task Execution

This is new relative to the existing (local, synchronous) execution-engine spec, and is the single biggest architectural addition this document makes.

- **Job queue** (e.g., a Postgres-backed queue to start — no need for a separate broker like Redis/RabbitMQ until volume actually demands it) holds dispatched agent tasks.
- **Background workers** (separate process/container from the API) pull tasks, execute, checkpoint progress to Memory, and report completion.
- **The Cloud API never blocks on a long task** — a phone message that triggers a multi-hour research task gets an immediate acknowledgment ("on it, I'll update you"), not a hung connection.
- **Progress updates** are pushed to the phone at meaningful checkpoints (not every tool call — that would be noise), defined per-task-type by the Planner when it decomposes the objective.

---

## 14. Error Handling, Observability, Deployment, Dev Environment, Testing, Repo & Docs Structure

These six carry over from the existing Master Construction Specification (Parts IX, XVI–XX, XXIII) with cloud-specific extensions only:

- **Error handling:** unchanged classify → understand → correct → retest → record-lesson loop, plus: a crashed worker must leave the task in a resumable state in Postgres, never silently lost.
- **Observability:** unchanged event log / cost tracking / status view, now queryable from the phone (`/status`, `/cost` style commands via the Telegram bot) rather than only via local log files.
- **Deployment:** cloud-first from the start — recommended stack: **Render** (or equivalent — Fly.io/Railway are the stated alternatives) for the API + worker processes, **Supabase or Render's managed Postgres** with pgvector, **object storage** for artifacts, **GitHub Actions** for CI, secrets in the host's secret manager. Staging and production are separate deployments; agents can reach staging autonomously, production requires the same approval-gate mechanism as any other consequential action.
- **Dev environment:** the PC remains the workshop — local dev still runs the same repo, same `pytest`, same `.env` pattern already established, against either a local Postgres (Docker) or a dev-tier cloud instance. Nothing about local development changes; what changes is that "done" now means "verified against the deployed cloud instance," not just "works on my machine."
- **Testing:** the existing three-level verification discipline (generated / tested-in-sandbox / verified-by-operator) gains a fourth practical checkpoint for cloud milestones: verified-by-operator **from their phone, against the deployed instance** — this is the real Level 3 for anything past Section 15's Milestone C.
- **Repo structure:** extends the existing tree —
  ```
  engine/
  ├── core/            (unchanged — model layer, memory, tools, agents, orchestrator)
  ├── apps/
  │   ├── cli/          (exists)
  │   └── telegram/      (new — bot webhook handler, thin client only)
  ├── workers/           (new — background job processing)
  ├── infra/             (new — deployment config, migrations, Docker)
  ├── tests/
  └── docs/              (unchanged six-file set, plus this document)
  ```
- **Documentation structure:** unchanged six standing docs, with this document added as the top-level pointer (`docs/00_MASTER_ARCHITECTURE.md` should be updated to point here, per the existing docs system's own rule that it's a pointer file, not a duplicate).

---

## 15. Milestone Sequence

This extends `docs/ROADMAP.md`, it doesn't replace the sessions already completed there. Milestones A–B below map directly onto the existing Milestone 1 (Sessions 1–5); Milestones C onward are new, extending toward the phone-first destination.

| Milestone | Deliverable | Definition of done | Depends on |
|---|---|---|---|
| **A** (existing M1, Sessions 1–2) | Model abstraction, 2 providers, CLI | ✅ Done — see `docs/PROJECT_STATE.md` | — |
| **B** (existing M1, Sessions 3–5) | Model registry, routing, retry/fallback | Registry resolves logical names; policy switch provably changes model; retry survives a transient failure | A |
| **C** | Persistent Project State in Postgres (cloud, not SQLite) | A Constitution created via CLI survives a redeploy | B |
| **D** | Telegram bot, text-only, single hardcoded task type | A message sent from a phone reaches the Orchestrator and a reply returns to the phone | C |
| **E** | Memory + RAG on real Postgres/pgvector | A question about ingested documents gets a grounded, cited phone reply | C, D |
| **F** | Job queue + background workers | A task dispatched from the phone completes after the phone app is closed and reopened | C, D |
| **G** | Tool system (web search, filesystem, one external API) | An agent-initiated tool call executes in a worker, result reaches the phone | E, F |
| **H** | Single-agent execution, unattended | The scholarship-research example (Section 2) completes end-to-end from the phone | F, G |
| **I** | Planner + task graph + Orchestrator dispatch | A one-paragraph objective becomes a task graph; multi-step task runs with correct sequencing | E, H |
| **J** | Approval gates, live on Telegram | An `approval_required` action blocks and resumes correctly via phone buttons | I |
| **K** | Multi-agent execution + verification separation | Creator/verifier separation demonstrably catches a deliberately broken output | I, J |
| **L (MVP — see Section 16)** | Full loop, phone-only operation, no PC required for normal use | All of Section 16's acceptance criteria pass | A–K |

**Sequencing rule:** no milestone starts before its dependencies show level-3 verification in `PROJECT_STATE.md`. This is the same discipline already in force — it doesn't relax because the destination got bigger.

---

## 16. Final Acceptance Criteria — Definition of "Done" for the MVP Personal AI OS

Not "the codebase exists." The following must all be true, verified from an actual phone against the actual deployed system:

- [ ] An objective sent as a phone message (text or voice) reaches the system and is acknowledged within seconds, even if the underlying task takes hours.
- [ ] The system asks clarifying questions only when genuinely needed (Critical/Important tier, per the existing question-prioritization rule) — not an interrogation.
- [ ] A multi-step task (research → decide → execute → report) completes with the phone app closed for part of the duration, and progress updates arrive without the operator polling.
- [ ] An approval-gated action (e.g., a production deploy or a spend above threshold) blocks correctly and resumes only after an explicit phone approval.
- [ ] The Adversarial/Critic mechanism demonstrably produces a "here's evidence against your assumption" response at least once during MVP testing — not just agreement.
- [ ] A deliberately broken agent output is caught by the verification layer before reaching the phone as a finished result.
- [ ] Killing a worker process mid-task does not lose the task — it resumes or reports failure cleanly, never silently disappears.
- [ ] The operator can ask "what's the status of X" and "what has this cost so far" from their phone and get an accurate answer.
- [ ] Switching the active model provider (e.g., Anthropic → a fallback) requires no code change and no redeploy — a config/env change only.
- [ ] None of the above required opening a terminal or sitting at the PC — the PC was used only during development of the system, not during its operation.

When all ten are checked, the MVP Personal AI Operating System exists. Everything past this point (native app, voice-first interaction, additional interfaces, deeper multi-agent sophistication) is a genuine extension, not a gap in the destination.
