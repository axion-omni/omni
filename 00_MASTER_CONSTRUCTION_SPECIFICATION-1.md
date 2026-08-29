# The AI Project Execution Engine
### Master Construction Specification — From Approved Architecture to Running Code

**Scope note on this document, stated up front rather than discovered later:** Parts I–VII, XI–XIV, and XXV — construction philosophy, the dependency graph, repo/stack decisions, the full capability ladder, Milestone 1's daily sessions, memory, agents, tools, the execution engine mapping, and the first working brick — are specified to *build-today* depth, and the first brick is not a description of code, it's actually built, tested, and committed (see the accompanying repo). Parts XV–XXIV (UI, infrastructure, CI/CD, observability, cost, security, self-improvement, future-proofing, docs, progress tracking) are specified to *solid reference* depth: complete, nothing omitted, but not daily-session-broken-out, because those layers become relevant starting around Milestone 5–6, months into the build — breaking them into Session-N detail now would be detail you can't act on yet and will likely need to revise once Milestones 1–4 teach you things this document can't predict. When you're approaching Stage 12, ask for those sessions broken out the same way Sessions 1–12 are here.

This is a companion, execution-focused document. The destination architecture it implements is `AI_Project_Execution_Engine.md` (already approved, not reproduced here). The learning path underneath it is the `AI_Mastery_Learning_Roadmap.md`. This document is the third leg: **how the destination actually gets typed into a repository, one 3-hour session at a time.**

---

## Part I — Construction Philosophy

**SMALL BRICK → VERIFY → COMMIT → CONNECT → EXPAND.**

Every brick, before it's built, answers seven questions — not as ceremony, as a filter that kills bad bricks before they cost you a session:

1. **What capability does this add?** If the answer is vague, the brick isn't scoped yet.
2. **Why does it exist in the final architecture?** If you can't point to a section in the destination document, don't build it.
3. **What does it connect to?** A brick with no connection point is a prototype, not a brick — fine occasionally, but name it as one.
4. **What must already exist first?** This is the dependency graph in Part II, applied locally.
5. **What exactly gets built?** Files, not vibes.
6. **How do you know it works?** A test that fails today and can pass by end of session — not "seems fine."
7. **What does the next brick depend on?** This is what makes tomorrow's session start immediately instead of starting with twenty minutes of "where was I."

**The standing rule that keeps this from becoming infrastructure-first paralysis:** the system must be continuously usable. After Session 1 (already built — see below), you can already call a model through the abstraction and get a typed response back. After Stage 4 (RAG), you can already ask it questions about your own documents. Nothing below waits for the "real" system to be finished before it does something real — each stage's deliverable is a working increment of the final thing, not a rehearsal for it.

---

## Part II — Master System Breakdown & Dependency Graph

Every layer, what it's responsible for, and — critically — what has to exist before it can be built.

| Layer | Purpose | Depends on |
|---|---|---|
| **Foundation** | Repo, env, config, testing harness, git discipline | — |
| **Model Layer** | Uniform interface to any model provider | Foundation |
| **Model Registry & Routing** | Pick the right model per task/cost policy | Model Layer |
| **Persistent State** | Project Constitution as a real, queryable record | Foundation |
| **Memory (RAG)** | Retrieval over documents/decisions/history | Persistent State, Model Layer |
| **Tool System** | Standard interface for search/filesystem/git/DB/etc. | Model Layer |
| **Single-Agent Execution** | One agent, one tool loop, real task | Model Layer, Tool System |
| **Verified Coding Agent** | Agent + tests + review, not just generation | Single-Agent Execution |
| **Planner** | Turns an objective into a task list | Memory, Model Layer |
| **Task Graph** | Dependency-aware task representation | Planner, Persistent State |
| **Orchestrator** | Decides "what runs next," assigns work | Task Graph, Single-Agent Execution |
| **Multi-Agent Execution** | Several specialized agents cooperating | Orchestrator, Tool System |
| **Browser/Computer Tools** | Real-world action beyond APIs | Tool System |
| **Automated Verification** | Creator ≠ verifier, structurally enforced | Multi-Agent Execution |
| **Human Approval Gates** | Permission tiers wired into the orchestrator | Orchestrator |
| **Deployment Automation** | CI/CD the agents can safely participate in | Verified Coding Agent, Approval Gates |
| **Monitoring/Observability** | See what's happening, what it costs | Orchestrator, all agents |
| **Self-Improving Workflows** | Measured, human-approved workflow changes | Monitoring, Decision Log |
| **General Execution Engine** | The full loop, any project type | Everything above |

Read bottom-to-top as "cannot be skipped," not top-to-bottom as "build in this order" — the actual build order is Part VI, which interleaves these because some (Memory, Tool System) need to exist earlier than their position in this dependency list would suggest, precisely so the system stays usable throughout.

---

## Part III — The Master Repository

```
engine/
├── core/                  # the engine itself — no UI, no product-specific code
│   ├── models/            # provider abstraction, registry, routing
│   │   └── providers/     # ONE file per provider SDK — nothing else imports them
│   ├── memory/            # project constitution, vector store, retrieval
│   ├── tools/             # standardized tool interface + implementations
│   ├── agents/             # agent definitions (role, prompt, tools, permissions)
│   ├── orchestrator/       # task graph, scheduler, dependency resolution
│   ├── execution/          # the Part XIV state machine: objective → deliverable
│   └── config.py
├── apps/                  # thin interfaces — CLI first, web/Telegram later
│   └── cli/
├── infra/                 # deployment, migrations, docker, CI config
├── tests/                 # mirrors core/ structure 1:1
├── docs/                  # the permanent documentation set (Part XXIII)
└── scripts/                # one-off / smoke-test scripts, never imported by core/
```

**Why this shape, and what must never leak across it:**
- `core/` never imports from `apps/` — the dependency arrow only points one way. This is what makes "same engine, five interfaces" (Part XV) possible instead of aspirational.
- `core/models/providers/` is the only place a provider SDK gets imported, anywhere. A grep for `import anthropic` outside that folder is a bug.
- `scripts/` is not `apps/` — scripts are for you, debugging and smoke-testing; apps are real interfaces other humans or systems use.
- No `services/` or `packages/` split yet — that's a distributed-systems shape for when this needs to scale past one process, which is not now. Introducing it early adds ceremony with no payoff at your current stage.

---

## Part IV — Technology Stack

| Layer | Primary | Alternative | Why | When to switch |
|---|---|---|---|---|
| Language (core) | Python 3.12 | TypeScript/Node | Deepest ecosystem for agents/RAG/eval tooling; free-tier friendly | If the orchestrator needs to live inside a Node-only deployment target |
| Model provider | Anthropic API | OpenAI, OpenRouter (multi-provider) | Strong tool-use + long context; abstraction (Part V) makes this non-permanent by design | Add providers via the registry as soon as Stage 2 lands — not a "switch," an "add" |
| Structured data | Pydantic | dataclasses only | Runtime validation for LLM structured outputs — needed the moment tool calling starts | Never, at this scale |
| Database | SQLite → PostgreSQL (Supabase) | Local Postgres via Docker | SQLite = zero setup for Stages 0–3; migrate once concurrent access or vector search matters | The moment Memory (Stage 4) needs pgvector |
| Vector store | pgvector (via Supabase) | Chroma (local, file-based) | One fewer moving part once on Postgres; Chroma is faster to start with, zero infra | Start with Chroma if you want Stage 4 running today; migrate at Stage 6+ |
| Agent orchestration | Hand-built primitive (Stage 7) → LangGraph (Stage 11) | CrewAI | Building the loop by hand first (per the Learning Roadmap's Layer 6) means you understand what LangGraph is abstracting when you adopt it | The moment manual state-tracking across >2 agents gets error-prone |
| Backend/API | FastAPI | Flask | Async-native, typed, pairs naturally with Pydantic, minimal ceremony | Not expected |
| Browser automation | Playwright | Selenium | Modern API, handles SPAs reliably, good Python bindings | Not expected |
| Hosting (dev) | Local machine | — | Zero cost while iterating on Stages 0–8 | — |
| Hosting (prod-ish) | Fly.io / Render free-to-cheap tier | Railway | Cheap always-on process for the orchestrator once agents run unattended | Stage 16 (Deployment Automation) |
| CI | GitHub Actions | — | Free for public/small private repos, integrates with the exact commit-checkpoint workflow this document assumes | — |
| Secrets | `.env` locally, provider's secret store in prod | Doppler/1Password if the team grows | Simplicity while it's one operator | If NEXA/C-Transit teams get engine access too |

**The lock-in rule that governs every row above:** nothing in `core/` is allowed to assume there's exactly one model provider, one database, or one hosting target. Where that's not yet literally true (there's one DB, one provider today), it's true in the sense that swapping it is a bounded, single-layer change — see Part XXII for exactly which files that touches per component.

---

## Part V — Model Abstraction and Routing

**Already built (Session 1):** `ModelProvider` interface, `ModelResponse`/`ModelCapabilities` contracts, `AnthropicProvider`.

**Not yet built — Stage 2 scope:**
- **Model registry** — maps a logical name (`"cheap-fast"`, `"reasoning-strong"`, `"coding"`) to an actual `(provider, model_id)` pair, read from config, not hardcoded in callers.
- **Capability registry** — per-model metadata (context window, tool support, cost) used by the router, seeded from `ModelProvider.capabilities()`.
- **Routing logic** — given a task type + `MODEL_POLICY` (free/cheap/balanced/quality/maximum), picks a logical model name. A simple rule table is enough at first; nothing ML-based is needed here.
- **Fallback** — if the primary provider raises `ModelUnavailableError` or `ModelRateLimitError`, retry once against a configured fallback provider before surfacing the failure.
- **Retry behavior** — exponential backoff, capped attempts, distinguishing retryable (`RateLimit`, `Timeout`, `Unavailable`) from non-retryable (`InvalidRequest`, `Auth`) errors — the exception hierarchy from Session 1 exists specifically to make this a five-line dispatch, not a guessing game.
- **Quota handling** — track calls/tokens per time window per provider; refuse gracefully (queue or downgrade model) rather than hammering a provider that's already rejecting requests.

A future model is added by: implement `ModelProvider`, register it in the capability registry, add it to the routing table. No caller-side code changes — that's the test of whether this layer actually did its job.

---

## Part VI — The Capability Ladder

Nineteen stages, organized by capability gained, not by technology. Each row is a real deliverable, testable, connected to what came before.

| # | Stage | Deliverable | Acceptance criteria |
|---|---|---|---|
| 0 | Dev foundation | Repo, env, config, test harness, git workflow | `pytest` runs green on an empty test |
| 1 | Basic AI interface | `ModelProvider` + one real provider | **DONE — see repo.** 4 tests passing |
| 2 | Model abstraction+routing | Registry, routing table, fallback, retry | Swapping `MODEL_POLICY` changes which model a fixed prompt hits, provably (log it) |
| 3 | Persistent project state | Project Constitution as a real record (SQLite) | Constitution created, read, updated across two separate process runs |
| 4 | Project memory (RAG) | Chunk → embed → store → retrieve pipeline | A real question about your own documents gets a grounded answer with a citation |
| 5 | Tool system | Standard tool interface + `search_web`, `read_file` | An LLM call requests a tool, tool executes, result returns to the model |
| 6 | Single-agent execution | One agent runs a real, multi-step task unattended | Given "compare 3 cloud DBs," produces a cited report with no manual step in between |
| 7 | Verified coding agent | Agent writes code + tests, a second pass reviews | Generated code's own tests are run and must pass before the brick is marked done |
| 8 | Planner | Objective → task list with acceptance criteria | Given a one-paragraph objective, produces a task list a human would recognize as reasonable |
| 9 | Task graph | Dependency-aware graph, not a flat list | Two independent tasks are identifiable as parallelizable; a blocked task is identifiable as blocked |
| 10 | Orchestrator | "What runs next" logic, single-threaded | Given the Stage 9 graph, correctly sequences execution respecting dependencies |
| 11 | Multi-agent execution | 2–3 specialized agents cooperate via the orchestrator | Researcher → Developer handoff happens with no manual copy-paste of context |
| 12 | Browser/computer tools | Playwright-backed tool, sandboxed | Agent completes a task requiring reading a live webpage it wasn't given the content of |
| 13 | Automated verification | Creator/verifier separation enforced structurally | A deliberately-broken output is caught by the verifier agent, not by you |
| 14 | Human approval gates | Permission tiers wired into orchestrator dispatch | An "approval required" action provably blocks until you respond |
| 15 | Deployment automation | CI/CD path an agent can use without unlimited authority | Agent-authored PR reaches staging automatically; production requires your click |
| 16 | Monitoring/observability | Logs, cost tracking, status dashboard (even CLI-based) | You can answer "what did yesterday's run cost, and what failed" without reading raw logs |
| 17 | Self-improving workflows | Measured workflow changes, human-approved | A workflow change is proposed with before/after metrics, not applied silently |
| 18 | General execution engine | Full Part XIV loop, project-type-agnostic | A non-software objective (e.g., a research brief) completes end-to-end through the same engine |

Stage numbering intentionally starts at 0 to match the accompanying repo, where Stage 0 (foundation) and Stage 1 (model interface) are already built and committed.

---

## Part VII — The 3-Hour Daily Build System (Milestone 1, in full)

Milestone 1 = "the system can communicate with models" = Stages 0–2. Sessions 1–2 below are **already implemented in the accompanying repo** — read them as the record of what was built, then continue from Session 3.

### Session 1 — Model abstraction + first provider — ✅ COMPLETE
- **Objective:** A uniform interface any caller can use, regardless of provider.
- **Why it matters:** Every later stage (routing, agents, tools) depends on never having to think about "which SDK" again.
- **Files created:** `core/models/base.py`, `core/models/exceptions.py`, `core/models/providers/anthropic_provider.py`, `core/config.py`, `tests/test_anthropic_provider.py`, `scripts/smoke_test.py`
- **Tests:** 4 unit tests against a fake client (no key/network needed) + a manual live smoke test script.
- **Result:** `pytest -v` → 4 passed.
- **Commit:** `c9925a1 — Session 1: model abstraction layer + Anthropic provider`.

### Session 2 — CLI entrypoint + config hardening — NEXT
- **Objective:** First end-to-end run from a terminal command, using the real provider (your actual key).
- **Why it matters:** Tests prove the contract; a CLI proves the *system*, with a human typing a real prompt and seeing a real answer, for the first time.
- **Prerequisites:** Session 1 committed (done). A real `ANTHROPIC_API_KEY` in your own `.env`.
- **Files to create:** `apps/cli/main.py`
- **Files to modify:** none
- **Implementation tasks:**
  1. `main.py` reads `sys.argv[1]` as the prompt (fall back to a usage message if missing).
  2. Load settings via `core.config.load_settings()`.
  3. Construct `AnthropicProvider(api_key=settings.anthropic_api_key)`.
  4. Call `.generate(prompt)`, print `result.text`, and print token usage to stderr (not stdout — keep stdout clean for piping later).
  5. Wrap the call in a `try/except ModelError` that prints a clean one-line error instead of a stack trace.
- **Tests:** one test using the same fake-client pattern as Session 1, asserting `main()` prints the expected text given a mocked provider (inject via a function parameter, not a global).
- **Expected result:** `python apps/cli/main.py "say hello"` prints a real Claude response.
- **Commit checkpoint:** `Session 2: CLI entrypoint, first real end-to-end run`.
- **Next session:** Session 3.

### Session 3 — Model registry (logical names → provider+model)
- **Objective:** Callers ask for `"cheap-fast"` or `"reasoning-strong"`, never a raw model string.
- **Prerequisites:** Session 2.
- **Files to create:** `core/models/registry.py`, `tests/test_registry.py`
- **Implementation tasks:** a `ModelRegistry` class holding `{logical_name: (provider_instance, model_id)}`; a `.resolve(logical_name) -> ModelProvider, model_id`; seed it with one entry pointing at the Anthropic provider from Session 1/2.
- **Tests:** resolving a known name returns the right pair; resolving an unknown name raises a clear error (not a `KeyError` leaking upward).
- **Expected result:** CLI from Session 2 can take an optional `--model cheap-fast` flag.
- **Commit checkpoint:** `Session 3: model registry`.
- **Next session:** Session 4.

### Session 4 — Routing table + MODEL_POLICY
- **Objective:** `MODEL_POLICY=cheap` and `MODEL_POLICY=quality` provably route the same task to different models.
- **Files to create:** `core/models/routing.py`, `tests/test_routing.py`
- **Implementation tasks:** a small rule table (task type × policy → logical model name); a `route(task_type, policy) -> logical_name` function; log the routing decision (this log line is what Stage 16's observability will eventually read).
- **Tests:** same task type under two different policies resolves to two different logical names.
- **Commit checkpoint:** `Session 4: policy-based routing`.
- **Next session:** Session 5.

### Session 5 — Retry + fallback
- **Objective:** A `RateLimitError` or `UnavailableError` doesn't kill the run.
- **Files to modify:** `core/models/registry.py` (wrap `.resolve()` usage in a retry helper), new `core/models/retry.py`
- **Implementation tasks:** exponential backoff (e.g., 1s/2s/4s, max 3 attempts) for retryable exceptions only; a configured fallback logical model tried once if all retries on the primary are exhausted.
- **Tests:** inject a fake provider that fails twice then succeeds → confirm the caller still gets a response; inject one that always fails → confirm fallback is attempted; inject a non-retryable error → confirm no retry happens (fails fast).
- **Commit checkpoint:** `Session 5: retry and fallback logic — Milestone 1 complete`.
- **Milestone check:** M1 acceptance criteria (below) — verify all three before moving to Stage 3.

**Milestone 1 acceptance criteria (must all be true before starting Stage 3):**
- [ ] `pytest -v` passes with zero failures, no network calls required.
- [ ] `python apps/cli/main.py "<prompt>"` returns a real response using your own key.
- [ ] Switching `MODEL_POLICY` in `.env` visibly changes which model handles an identical request, confirmed via the routing log line.

Sessions 6+ (Stage 3 — Persistent Project State, and onward) follow the same fixed shape as Sessions 1–5 above. Ask for them broken out once Milestone 1's three checkboxes are real — that's the natural checkpoint, and building Session 6 today would mean designing against a routing layer that doesn't exist yet.

---

## Part VIII — Build Checkpoints (Milestones)

| # | Milestone | Acceptance criteria |
|---|---|---|
| 1 | Can communicate with models | See Part VII, above — in progress, Session 2 of 5 next |
| 2 | Has persistent project memory | A Project Constitution survives a process restart and is queryable |
| 3 | Can retrieve knowledge | A real question about uploaded documents gets a grounded, cited answer |
| 4 | Can use tools | A model-initiated tool call executes and its result reaches the model |
| 5 | Can execute a task | An unattended multi-step task (Stage 6) completes with no manual intervention |
| 6 | Can build and test software | A verified coding agent (Stage 7) ships code whose own tests pass before being marked done |
| 7 | Can plan a project | A one-paragraph objective becomes a task graph a human recognizes as sane |
| 8 | Can orchestrate workers | Two+ agents hand off work through the orchestrator with no manual context copy |
| 9 | Can autonomously execute bounded projects | A small real project (not a toy) completes end-to-end with only approval-gate interventions |
| 10 | General project execution platform | A non-software objective completes through the same engine, unmodified |

---

## Part IX — Testing (designed in from Session 1, not appended later)

Per component:

| Test type | What it covers | Where it already exists |
|---|---|---|
| Unit | One function/class, mocked dependencies | `tests/test_anthropic_provider.py` — mocked client |
| Integration | Real components talking to each other, still no live network unless explicit | Introduced at Stage 3 (state + memory talking to each other) |
| Failure | Deliberately broken input/dependency, confirms graceful failure | `test_sdk_rate_limit_error_is_translated`, `test_missing_api_key_raises_model_auth_error` |
| Security | Injection, permission bypass attempts | Introduced at Stage 5 (Tool System) — a tool is the first real attack surface |
| AI behavior | Does the *output* meet criteria, not just "did it run" | Introduced at Stage 6 — needs an evaluation harness, not just pass/fail |
| Regression | A fixed bug stays fixed | Ongoing, added per bug from Stage 3 onward |

**Creator/verifier separation**, structurally, starting at Stage 13:
```
CREATOR → TESTER → CRITIC → REPAIR → RETEST
```
Before Stage 13 exists, this same principle already applies at the human level: you are the tester and critic for every session's output. Don't relax that discipline just because the formal agent-verifier doesn't exist yet — Session 2 through 12's acceptance criteria exist specifically so you're never the one deciding "looks done" from vibes.

---

## Part X — Human-in-the-Loop Permission Model

| Tier | Meaning | Examples |
|---|---|---|
| **Autonomous** | No approval needed, reversible | Generate code, run tests, write to local files, staging deploys |
| **Notify** | Happens, then you're told | Non-critical refactor, routine research summary |
| **Approval required** | Blocks until you respond | Production deploy, spending above a threshold, sending external communication |
| **Human only** | No agent authority at all, ever | Deleting a database, legal/financial commitments, changing the permission model itself |

Implementation mechanism (built at Stage 14, designed now so nothing above it needs retrofitting): every tool and agent action carries a declared tier in its definition. The orchestrator checks the tier before dispatch — an `approval_required` action creates a pending-approval record and halts that branch of the task graph until you respond (CLI prompt initially; a real approval queue UI comes with Stage 15+/Part XV). The goal stated plainly: **maximum useful autonomy with controlled risk** — not maximum autonomy, and not zero.

---

## Part XI — Persistent Project Memory

What must survive: constitution, requirements, decisions, research, assumptions, unknowns, task state, failures, lessons, architecture, artifacts, agent outputs, evaluation results.

**Storage split:**
- **Relational (SQLite → Postgres):** structured facts with clear schema — tasks, decisions, status, costs. Queryable exactly (`SELECT * WHERE status = 'blocked'`).
- **Vector (Chroma → pgvector):** unstructured text needing similarity search — research findings, past agent reasoning, documents.
- **Documents/artifacts:** actual files (code, reports, designs) on disk or object storage, referenced by path/ID from the relational store — never duplicated into the vector store as raw blobs.

**How tomorrow's agent understands today without loading everything:** the Project Constitution (Part II of the Execution Engine doc) is always loaded in full — it's deliberately kept small (a page, not a transcript). Everything else is retrieved on demand: a summarization step condenses old task history into a few sentences once a task is closed, and the *summary*, not the full transcript, is what gets embedded and retrieved. Full transcripts stay archived and retrievable by ID for the rare case an agent needs to dig in, but they aren't loaded by default. This is context assembly, not context dumping — the same discipline that keeps a $200/day agent budget from becoming a $2,000/day one.

---

## Part XII — Agent System

Initial roster (introduced across Stages 6–13, not all at once):

| Agent | Introduced | Inputs | Outputs | Tools | Termination |
|---|---|---|---|---|---|
| Researcher | Stage 6 | Question | Cited findings | web search, doc fetch | Answer produced or max iterations hit |
| Developer | Stage 7 | Task + spec | Code + tests | filesystem, terminal, git | Tests pass or blocked → escalate |
| Tester | Stage 7 | Code | Pass/fail + report | terminal (test runner) | Deterministic — no "reasoning" needed |
| Critic/Reviewer | Stage 13 | Artifact + acceptance criteria | Approve/reject + reasons | read-only tools only | Explicit verdict required, no "looks fine" |
| Architect | Stage 8 (as part of Planner) | Objective | Spec + task breakdown | memory retrieval | Spec accepted by human or Critic |
| Security reviewer | Stage 13 | Code touching auth/data | Pass/fail + findings | static analysis tools, read-only | Explicit verdict |
| Orchestrator | Stage 10 | Task graph state | Next dispatch | none (coordinates, doesn't execute) | N/A — long-running |

**Rule enforced from the start:** an agent is created only when separation provides real value (verification independence, specialization depth) — not because a roster looks impressive. Notice the roster above is five agents, not the twelve+ roles sketched conceptually in the destination architecture; the rest (documentation worker, deployment agent, project manager, marketing worker) get added at the stage where a real task needs them, per Part XIII of the destination doc — not pre-built speculatively.

---

## Part XIII — Tool System

Standard shape, every tool, from Stage 5 onward:

```python
class Tool(ABC):
    name: str
    permission_tier: PermissionTier   # autonomous | notify | approval_required | human_only
    input_schema: dict                 # JSON schema, validated before execution
    def execute(self, **kwargs) -> ToolResult: ...
```

Initial tools, in build order: `read_file`, `write_file` (approval_required outside a sandboxed workdir), `web_search`, `run_tests`, `git_commit` (notify tier), `git_push` (approval_required), `http_request`.

New capability = new tool implementing this interface, registered in a tool registry the orchestrator reads — never a change to the orchestrator itself. That's the acceptance test for whether this layer is doing its job, same pattern as the model registry in Part V.

---

## Part XIV — Project Execution Engine (implementation mechanism per transition)

| Transition | Implementation mechanism | Stage that builds it |
|---|---|---|
| Objective → Understanding | Structured intake form (Part I fields) parsed into the Constitution | Stage 3 |
| Understanding → Questions | LLM call against the Constitution, filtered by the 4-tier priority rule | Stage 8 |
| Questions → Research | Each open question becomes a Researcher task in the task graph | Stage 8–9 |
| Research → Decisions | Options + recommendation formatted, presented via approval gate | Stage 9, 14 |
| Decisions → Specification | Template selected by project type, filled from Constitution + decisions | Stage 8 |
| Specification → Task Graph | Decomposition prompt + dependency inference | Stage 9 |
| Task Graph → Delegation | Orchestrator dispatch loop | Stage 10 |
| Delegation → Execution | Agent runs, tool loop | Stage 6–7, 11 |
| Execution → Verification | Creator/verifier separation | Stage 13 |
| Verification → Integration | Merge/assembly step, itself tested | Stage 13 |
| Integration → Deployment | CI/CD pipeline, approval-gated | Stage 15 |
| Deployment → Monitoring | Observability hooks fire on every stage transition | Stage 16 |
| Monitoring → Learning | Post-task analysis written to lessons store | Stage 17 |
| Learning → Replanning | Failed/blocked tasks re-enter the graph, modified | Stage 9–10, 17 |

Every row in this table is the difference between the destination diagram and something that runs — this is the table to revisit any time a stage feels underspecified.

---

## Part XV — User Interface (progressive)

**Start:** CLI (Session 2, already scoped above). It's the entire interface through Milestone 4.

**Add when justified, not before:**
- **Web dashboard** — once there's a task graph worth visualizing (Stage 9+) and an approval queue worth seeing (Stage 14+).
- **Telegram** — cheapest way to get approval-gate notifications on your phone; worth adding around Stage 14, before a full web UI, because it's a few hours of work for a large usability jump.
- **Voice** — no clear need until the engine is trustworthy enough to interact with hands-free; not before Milestone 8.
- **Task graph / agent activity visualization** — part of the web dashboard, not a separate interface.

**The constraint that makes all of this cheap later:** every interface talks to `core/` through the same API (FastAPI, introduced alongside the web dashboard) — never by importing `core/` directly into UI code. This is Decision D003 in the repo's decision log, made now specifically so it's free to honor later.

---

## Part XVI — Infrastructure

| Component | Runs where (now) | Runs where (later) |
|---|---|---|
| Core engine | Local machine | Fly.io/Render, always-on process |
| Database | SQLite file, local | Supabase Postgres |
| Vector store | Chroma, local file | pgvector on the same Supabase instance |
| Model calls | Direct to Anthropic API | Unchanged — always remote by nature |
| Secrets | `.env`, local, gitignored | Host platform's secret manager |
| Logs | stdout/local file | Shipped to a log aggregator (even a free-tier one) once agents run unattended |

**Why local-first works on weak hardware:** nothing through Milestone 4 requires local compute beyond running Python and SQLite — the actual intelligence is remote (the model API). The only local-hardware-sensitive stage is Stage 12 (browser automation, Playwright needs a real browser process) — budget for that specifically, everything before it runs on effectively any machine.

---

## Part XVII — CI/CD and Version Control

```
CODE → GIT → TEST (CI) → BUILD → STAGING (auto) → VERIFICATION → APPROVAL → PRODUCTION
```

Agents participate up through STAGING without restriction (Autonomous/Notify tier — see Part X). Everything from VERIFICATION onward requires the Approval-required tier: an agent can open a PR, an agent can deploy its own PR to staging, but only a human click promotes staging to production. This is enforced by making the production-deploy tool itself declared `approval_required` in its Tool definition (Part XIII) — the restriction lives in the tool, not in agent instructions that could be prompt-injected around.

---

## Part XVIII — Observability

Minimum viable answer to "what is happening" (Stage 16, but the logging *hooks* get added incrementally from Stage 2 onward, per the routing-decision log line already specified in Session 4):

- **Event log:** every model call, tool call, and agent handoff — timestamp, actor, action, result, cost, latency.
- **Status view:** current task graph state (CLI table until the web dashboard exists).
- **Cost-to-date:** running total per project, per day — sourced from the event log, not a separate system.
- **"What's blocked":** derived query over the task graph — tasks with unmet dependencies or pending approvals.

Nothing here needs a dedicated observability platform before Milestone 6 or so — a structured (JSON-lines) log file and a couple of query scripts cover it until scale actually demands more.

---

## Part XIX — Cost Control

Policies (`MODEL_POLICY`, already wired into Session 4's routing): `free` (local/free-tier models only) · `cheap` · `balanced` · `quality` · `maximum` (frontier only, ignore cost).

Tracked from Stage 2 onward (it's a direct byproduct of `ModelResponse.total_tokens`, already returned by every provider call since Session 1): tokens per call, cost per call (using the `cost_per_million_*` fields already in `ModelCapabilities`), rolled up to cost per task and cost per project. Retries and failed calls are tracked and counted against cost — a silently-retried expensive call is exactly the kind of thing this exists to catch.

---

## Part XX — Security

| Concern | Mechanism | Stage introduced |
|---|---|---|
| API keys/secrets | `.env`, gitignored, never logged | Stage 0 (already enforced) |
| Agent permissions | Tool-level permission tiers | Stage 5, 14 |
| Sandboxing | Filesystem tools scoped to a workdir; terminal tool scoped/restricted | Stage 5, 7 |
| Prompt injection | Tool results treated as untrusted data, never re-interpreted as instructions | Stage 5 |
| Malicious documents | RAG ingestion strips/flags executable content, doesn't execute anything from ingested text | Stage 4 |
| Tool abuse | Rate limits + permission tiers per tool, not just per agent | Stage 5, 14 |
| Data isolation | Per-project memory namespacing — one project's memory never leaks into another's retrieval | Stage 3–4 |
| Audit logs | Every approval-gated action logged with who/what/when/result | Stage 14, 16 |
| Destructive actions | Human-only tier, enforced at the tool definition, not the prompt | Stage 5, 10 |

Assume, from Stage 5 onward, that the system will eventually hold real tool power — building the permission model in at that stage costs almost nothing; retrofitting it after Stage 12 (browser tools, real external action) would mean auditing everything already built.

---

## Part XXI — Self-Improvement

Four distinct things, deliberately kept separate:

| Term | Meaning | Human role |
|---|---|---|
| **Self-monitoring** | System reports its own performance/cost/failures | Read-only for you |
| **Self-optimization** | System proposes a workflow change with before/after metrics | You approve or reject |
| **Self-modification** | System changes its own code/prompts based on that approval | Only executes after explicit approval, never silently |
| **Self-replication** | System spins up new instances of itself | **Out of scope for this build.** Not a Stage. Not planned. |

Stage 17 builds the first three. The fourth is excluded intentionally — the destination architecture (Part XXI of the source doc) requires the system to "remain human-controlled," and self-replication is the one capability that most directly threatens that property. This isn't a technical limitation; it's a line drawn on purpose.

---

## Part XXII — Future-Proofing

| Swappable | Abstraction boundary | Files touched to swap |
|---|---|---|
| Model/provider | `ModelProvider` interface | One new file in `providers/`, one registry entry |
| Database | Repository pattern over `core/memory/store.py` (introduced Stage 3) | One new store implementation |
| Vector store | Same repository pattern, retrieval interface | One new implementation, embeddings stay provider-agnostic |
| Hosting | 12-factor config (env vars only, no hardcoded paths) from Stage 0 | Deployment config only, zero application code |
| Agent framework | Hand-built orchestrator (Stage 10) behind the same `Orchestrator` interface LangGraph would later implement | Orchestrator internals only, task/agent contracts unchanged |
| Tool providers | `Tool` interface (Part XIII) | One new tool file, registry entry |
| UI | Everything behind the FastAPI layer (Part XV) | New `apps/` entry only |

Every "swap" in this table costs one new file plus one registration line — that's the actual test of whether an abstraction earned its place, and it's why Parts V, XIII, and XV were specified as interfaces before anything else was built on top of them.

---

## Part XXIII — Documentation System

```
docs/
├── 00_MASTER_ARCHITECTURE.md      # pointer to the approved destination doc
├── 01_SYSTEM_SPECIFICATION.md     # this document, or a living version of it
├── 02_TECH_STACK.md               # Part IV, kept current as choices evolve
├── 03_REPOSITORY_STRUCTURE.md     # Part III, updated as folders are added
├── 04_DATABASE.md                 # schema, written starting Stage 3
├── 05_AGENT_SPECIFICATIONS.md     # Part XII, one entry per agent as built
├── 06_TOOL_SPECIFICATIONS.md      # Part XIII, one entry per tool as built
├── 07_ORCHESTRATOR.md             # written at Stage 10
├── 08_MEMORY.md                   # Part XI, written at Stage 3-4
├── 09_SECURITY.md                 # Part XX, updated per stage
├── 10_TESTING.md                  # Part IX, updated per stage
├── 11_DEPLOYMENT.md               # written at Stage 15
├── 12_PROGRESS.md                 # ALREADY LIVE — see repo
├── 13_DECISION_LOG.md             # ALREADY LIVE — see repo, 3 entries so far
├── 14_CHANGELOG.md                # one line per commit, human-readable
└── 15_FUTURE_ROADMAP.md           # open ideas not yet scheduled into a stage
```

Files not yet needed (04–11, 14–15) get created at the stage that first needs them, not stubbed empty now — an empty doc file is worse than no file, because it looks maintained when it isn't.

---

## Part XXIV — Progress Tracking

Machine-readable (`docs/progress.json`, already live in the repo) and human-readable (`docs/12_PROGRESS.md`, already live) versions of the same state, kept in sync by hand at each commit — automating that sync is itself a reasonable Stage 16 candidate, not before.

Schema (already in use):
```json
{
  "overall_progress_pct": 3,
  "current_milestone": "...",
  "current_stage": "...",
  "current_brick": "...",
  "completed_bricks": [{"id": "...", "title": "...", "files": [...], "tests_passing": 4, "commit": "..."}],
  "next_brick": "...",
  "blocked_bricks": [],
  "open_questions": [],
  "open_risks": [],
  "decisions_required": [],
  "failed_experiments": []
}
```

---

## Part XXV — The First Implementation (already done — this is the record of it)

1. **What we built:** the Model Abstraction Layer + first real provider (Anthropic).
2. **Why:** every later stage depends on never touching a provider SDK directly again.
3. **Exact stack:** Python 3.12, `anthropic` SDK, `pytest`, `python-dotenv`, `pydantic`.
4. **Exact files:** `core/models/base.py`, `core/models/exceptions.py`, `core/models/providers/anthropic_provider.py`, `core/config.py`, `tests/test_anthropic_provider.py`, `scripts/smoke_test.py`, plus `docs/12_PROGRESS.md`, `docs/progress.json`, `docs/13_DECISION_LOG.md`.
5. **Folder structure:** as specified in Part III, initial slice only (`core/models/`, `core/config.py`, `tests/`, `docs/`, `scripts/`).
6. **Implementation steps:** ModelResponse/ModelCapabilities dataclasses → ModelProvider ABC → AnthropicProvider with lazy SDK import and full error translation → Settings/config loader → tests against a fake client → live smoke-test script.
7. **Exact commands:**
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   pytest -v
   ```
8. **Tests:** 4, all passing, zero network dependency (see full run output below).
9. **Expected output:** `4 passed in 0.03s`.
10. **Acceptance criteria:** met — uniform response shape returned; auth error raised on missing key; provider-specific errors translated to the shared exception hierarchy; capabilities correctly reported.
11. **Git commit point:** `c9925a1` — already committed.
12. **What becomes possible after this brick:** every subsequent stage — routing, memory, tools, agents — can now say "call the model" without ever importing an SDK again.
13. **Next brick:** Session 2, CLI entrypoint — fully specified in Part VII above, ready to start immediately.

**Actual test run, for the record:**
```
collected 4 items
tests/test_anthropic_provider.py::test_generate_returns_uniform_model_response PASSED
tests/test_anthropic_provider.py::test_missing_api_key_raises_model_auth_error PASSED
tests/test_anthropic_provider.py::test_sdk_rate_limit_error_is_translated PASSED
tests/test_anthropic_provider.py::test_capabilities_reports_context_window PASSED
4 passed in 0.03s
```

The repository containing this — real code, real tests, a real commit — ships alongside this document. Add your own `ANTHROPIC_API_KEY` to `.env`, run `pytest -v` yourself to confirm it on your machine, then start Session 2.
