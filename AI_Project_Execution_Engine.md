# The AI Project Execution Engine
### Master Blueprint / Construction Manual

**Core transform:**

```
Intent → Understanding → Specification → Decomposition → Research →
Planning → Execution → Verification → Integration → Deployment → Monitoring
```

This is not a chatbot and not an "AI assistant." It's a general-purpose **project execution system**: you supply an objective and constraints, and the system converts that into a living execution graph — asking for human decisions only where human judgment is actually required, researching unknowns on its own, delegating work to specialized AI workers, verifying their output independently, integrating the pieces, and delivering a finished, tested result.

It works the same way whether the project is a software product, a business, a marketing campaign, an engineering build, a research report, a final-year project, or a physical product. **Only the specialized workers and tools change — the operating procedure stays fixed.** That's what makes it worth building once, properly, instead of improvising a new process per project.

---

## The Three-Layer Architecture

```
LAYER 1 — YOU
Vision → Judgment → Approval → Strategy
                │
                ▼
LAYER 2 — ORCHESTRATOR
Planning → Decomposition → Delegation → Monitoring → Replanning
                │
                ▼
LAYER 3 — WORKFORCE
Researcher · Coder · Designer · Analyst · Tester · Marketer · Reviewer
                │
                ▼
INFRASTRUCTURE
Models + APIs + RAG + databases + Git + browsers + compute + cloud + automation + external services
```

You own vision and approval. The Orchestrator owns sequencing. The Workforce owns execution. Nothing skips a layer — a worker never gets to redefine the objective, and the Orchestrator never gets to make an irreversible call on your behalf.

---

## 1. Start With the Objective

Before anything is built, the system captures — from the human, explicitly, not inferred:

| Field | Question it answers |
|---|---|
| Objective | What are we trying to accomplish? |
| Why | Why does it need to exist? |
| Desired outcome | What does "finished" look like? |
| Constraints | Budget, technology, geography, deadline, regulations, resources |
| Available resources | Money, people, APIs, hardware, existing software, data |
| Preferences | How the solution should behave |
| Non-negotiables | What the system must never violate |
| Known information | Everything the human already knows |
| Unknown information | What the human doesn't know yet |

**Rule: the system does not start building until it has established whether it understands the objective.** Skipping this step is the single most common reason AI-assisted projects drift — the build starts, momentum takes over, and nobody goes back to check it still matches the original intent.

---

## 2. The Project Constitution

Every project gets one persistent document — its source of truth. Every agent reads it before acting; every major decision updates it.

```
PROJECT CONSTITUTION
├── Mission
├── Purpose
├── Desired outcome
├── Success criteria
├── Constraints
├── Assumptions
├── Non-negotiables
├── Available resources
├── Known facts
├── Unknowns
├── Risks
├── Decisions
└── Change history
```

**Implementation note:** this is a markdown file (or a small structured record) in whatever memory layer you're already running — a vector-searchable project-memory store works well here, so any agent can retrieve the relevant constitution section without loading the whole document into every context window. Treat it as versioned, not editable-in-place: every change is an addition to the change history, never a silent overwrite.

---

## 3. Interrogate the Human — Sparingly

The system finds the gaps in the constitution and asks about them — but a 200-question intake form kills the whole premise. Questions are triaged:

| Tier | Meaning |
|---|---|
| **Critical** | Cannot proceed without an answer |
| **Important** | Would materially change the architecture or outcome |
| **Useful** | Would improve the solution, not blocking |
| **Optional** | Can be decided later, or defaulted |

Ask the minimum number of high-value questions. Everything below "Important" gets a reasonable default, stated explicitly, rather than a question.

---

## 4. Separate Known From Assumed

Every fact in the system carries one of six labels, always visible, never collapsed into plain narrative:

```
Known → Assumed → Unknown → Needs research → Needs experimentation → Requires human decision
```

**This is the load-bearing discipline of the whole engine.** An AI assumption that quietly becomes treated as a project fact is exactly how a system confidently builds the wrong thing for three weeks. If a worker can't cite where a fact came from, it isn't a fact yet — it's an assumption, and it gets labeled as one.

---

## 5. The Research Queue

Every unknown becomes a tracked research item with a fixed shape:

```
UNKNOWN:    [the open question]
ACTION:     [what will be investigated, and how]
OUTPUT:     [research report + sources + confidence level]
DECISION:   [autonomous | human approval required]
```

Anything that doesn't require human judgment gets investigated without waiting on you. Anything that does gets queued for a decision gate (Section 7).

---

## 6. Research Workers

Research agents search the web, read documentation, compare technologies, investigate competitors and regulations, inspect APIs, and analyze pricing — but the deliverable is never prose alone. Every substantive research result returns this shape:

```
Question → Finding → Evidence → Source → Confidence → Implication → Recommendation → Remaining unknowns
```

**Implementation note:** this maps directly onto a research agent built with tool-calling + web search + a citation-tracking step (see Part IV/V of the Field Manual — structured outputs and function calling are what make "Evidence" and "Source" machine-checkable instead of just asserted).

---

## 7. Human Decision Gates

Research resolves into a decision, presented as a real choice, not a recommendation dressed as a fait accompli:

> **Investigated:** three database architectures.
> - **Option A** — cheap, simple, scalable
> - **Option B** — more powerful, more complex
> - **Option C** — best performance, most expensive
>
> **AI recommendation:** B, because [reasoning].
> **Decision required:** A / B / C.

The human's choice is written into the Project Constitution's decision log — permanently, with the reasoning attached, so no future agent re-litigates it from scratch.

---

## 8. Generate the Specification

Once uncertainty is reduced enough, the system produces the actual spec — shaped by project type:

- **Software:** requirements, architecture, database, APIs, interfaces, authentication, security, testing, deployment
- **Business:** customer, value proposition, operations, pricing, distribution, marketing, economics
- **Engineering:** requirements, components, electrical/mechanical architecture, firmware, testing, manufacturing

The engine picks the right template dynamically — it doesn't force a software spec onto a marketing campaign.

---

## 9. Decompose the Project

The core transform: one large objective becomes a tree of workstreams and tasks.

```
PROJECT
├── Workstream A → Task, Task, Task
├── Workstream B → Task, Task, Task
├── Workstream C → Task, Task
└── Integration
```

Every task carries a fixed set of fields — none optional:

`objective · inputs · expected output · dependencies · responsible agent · tools · acceptance criteria · status · priority · estimated complexity`

A task without acceptance criteria is not a task yet — it's an intention.

---

## 10. Build the Dependency Graph

Not a checklist — a graph. What blocks what, and what can run in parallel:

```
Requirements
     ↓
Architecture
     ↓
Database ──────┐
     ↓         │
Backend ───────┤
     ↓         │
API ───────────┤
     ↓         ↓
Frontend → Integration → Testing → Deployment
```

Tasks with no unmet dependency run in parallel automatically. Tasks blocked on unfinished work wait — and the Orchestrator is what tracks which is which (Section 12).

---

## 11. Specialized Workers

One AI given every responsibility at once produces shallow work across all of them. Split by role instead:

| Worker | Job |
|---|---|
| Architect | Designs the system |
| Researcher | Finds information |
| Developer | Builds |
| Designer | Designs interfaces |
| Data specialist | Designs data structures |
| Tester | Tries to break things |
| Security reviewer | Looks for vulnerabilities |
| Analyst | Evaluates evidence |
| Documentation worker | Maintains project knowledge |
| Marketing worker | Handles market-facing work |
| Project manager | Coordinates |

The exact roster changes per project — a physical-product build swaps in a mechanical/electrical designer; a research project drops most of the software roles. What doesn't change is the principle: **narrow roles, explicit handoffs.**

---

## 12. The Orchestrator

Sits above every worker. Its job is not to do the work — it's to answer, continuously: **what needs to happen next?**

It watches project state, dependencies, completed tasks, failures, open research, pending decisions, resources, and deadlines, then assigns the next appropriate task to the right worker.

**Implementation note:** this is the piece an orchestration framework (LangGraph for state-machine precision, or CrewAI for a faster-to-stand-up role-based version) is actually for. The Orchestrator is the graph; the workers are the nodes.

---

## 13. Every Worker Operates Under a Contract

No worker is allowed to just report "Done." Every completed task returns:

```
TASK          — what was requested
WORK PERFORMED — what was actually done
OUTPUT        — what was produced
EVIDENCE      — how we know it works
TESTS         — what was tested
FAILURES      — what didn't work
ASSUMPTIONS   — what was assumed
RISKS         — what could be wrong
NEXT ACTION   — what should happen next
```

This single contract is what prevents the most common agentic failure mode: an agent that confidently reports success while having done nothing verifiable.

---

## 14. Verification Is Never Done by the Creator

**The agent that builds something must not be the same agent that decides it's correct.**

| Domain | Creation → Verification |
|---|---|
| Software | Developer → Tester → Reviewer |
| Research | Researcher → Evidence checker → Analyst |
| Business strategy | Strategist → Critic → Decision-maker |
| Engineering | Designer → Simulation/test → Reviewer |

This is worth over-engineering slightly, because it's the single control that catches the failure mode every other safeguard misses: a confidently wrong answer that *sounds* right to the model that produced it.

---

## 15. The Adversarial Worker

Every project gets one agent whose only job is to try to prove the project wrong:

- What assumptions are false?
- What could fail?
- What did we overlook?
- What happens at scale, or under hostile conditions?
- What happens if our core assumption is wrong?
- Is there a simpler solution?
- Is this economically viable at all?

Not there to make the project feel validated. There to break it before reality does, while breaking it is still cheap.

---

## 16. Nothing Is "Finished" Until It Passes Acceptance Criteria

```
Software:  Build → Unit tests → Integration tests → Security checks → Human review → Deploy
Physical:  Design → Simulation → Prototype → Measurement → Stress testing → Revision
```

Generation is not completion. An AI producing output is the start of a task, not the end of one.

---

## 17. Human Approval, Used Strategically

Approving every micro-action defeats the point of automation. Set thresholds instead:

| Tier | Meaning | Example |
|---|---|---|
| **Autonomous** | Low-risk, reversible | Generate code, run tests, deploy to staging |
| **Notify** | AI acts, tells you after | Non-critical refactor, minor content edit |
| **Approval required** | Important, irreversible | Deploy to production, spend $500 |
| **Human-only** | High-risk, no AI authority at all | Delete a database, sign a legal commitment |

Set these thresholds once, per project, at the start — not improvised mid-execution when something is already halfway shipped.

---

## 18. Project Memory

Persistent, not session-bound:

`Project Constitution · Decision Log · Research Knowledge · Architecture · Task Graph · Artifacts · Failures · Lessons`

No new agent — and no future you, six weeks later — should have to reconstruct why the project exists or why a decision was made. If it isn't written to memory, it will be forgotten and re-litigated.

---

## 19. Version Everything

`Code → Git` · `Documents → version history` · `Decisions → decision log` · `Architecture → versioned snapshots`

The system must always be able to answer: **why is it built this way?** — with a specific decision entry, not a shrug.

---

## 20. Continuous Replanning

The plan is not static. When a task fails, the system evaluates why, then chooses: retry, modify the task, research further, ask the human, redesign the dependency, or abandon the approach — and updates the graph accordingly.

```
Plan → Execute → Observe → Replan → (repeat)
```

A system that can't replan isn't executing a plan — it's just following a script until it breaks.

---

## 21. Failure Management

```
Failure → Classify → Understand cause → Attempt correction → Retest → Record lesson
```

Set retry limits. Escalate anything that fails persistently instead of looping on it silently — an agent stuck retrying the same broken approach ten times is a cost leak, not diligence.

---

## 22. Knowing When to Stop

"Finished" is a conjunction, not a vibe:

```
Requirements satisfied
  AND acceptance tests passed
  AND critical risks addressed
  AND documentation complete
  AND deployment completed (where applicable)
  AND human approves the final result
→ PROJECT COMPLETE
```

---

## 23. Deliverable Generation

Output shape follows project type:

- **Software:** source code, build/executable, documentation, deployment instructions, tests
- **Business:** strategy, operating procedures, financial model, marketing assets, execution plan
- **Engineering:** specifications, designs, BOM, firmware, testing procedures, documentation

---

## 24. Post-Project Analysis

After delivery, the system interrogates itself: what worked, what failed, what took too long, which agents underperformed, which decisions were wrong, what could be automated next time, what reusable components emerged. The lessons get stored — the next project starts smarter, not from zero.

---

## 25. The System Builds Its Own Reusable Library

Successful projects leave behind reusable assets: auth modules, payment integration, database templates, research workflows, marketing workflows, testing frameworks, agent prompts, API connectors, UI components, deployment scripts, business templates, engineering calculations.

**This is where compounding actually happens.** Project 5 should take a fraction of the effort Project 1 took, not because the model got smarter, but because the library did.

---

## 26. The Universal Execution Loop

```
HUMAN OBJECTIVE
      ↓
   UNDERSTAND → QUESTION → RESEARCH → HUMAN DECISIONS
      ↓
SPECIFICATION → DECOMPOSITION → DEPENDENCY GRAPH
      ↓
DELEGATE WORK → EXECUTE → VERIFY → INTEGRATE → TEST
      ↓
HUMAN REVIEW → DEPLOY → MONITOR → LEARN → REPLAN
      │
      └──────────────────────────────────→ repeat
```

Every section above is a component of this one loop. None of them work in isolation — the Adversarial Worker (15) is only useful because Verification (14) already separated creation from judgment; Replanning (20) is only possible because Project Memory (18) preserved why the original plan existed.

---

## 27. The Design Principle That Makes This Different

Don't build a system whose purpose is:

> "Ask AI to build things."

Build a system whose purpose is:

> "Convert objectives into verified outcomes."

The engine doesn't care whether the input is *"build a mobile app"*, *"launch a transportation company,"* or *"complete a final-year engineering project."* It receives **objective + constraints + resources + desired outcome**, and produces **research + decisions + plan + execution + verification + deliverable.** The abstraction is the point — it's what lets the same system run every project you'll ever start, instead of you rebuilding the process from scratch each time.

---

## 28. Worked Walkthrough — Applying the Engine

Two examples of what the interface feels like once this is running, using an objective close to what you'd actually type:

```
PROJECT: Add offline tap-to-ride payment to C-Transit for the Gidan Kwano route.
WHY: Riders lose trips to poor connectivity at peak hours; drivers lose revenue to failed taps.
BUDGET: [your figure]
DEADLINE: [your date]
CONSTRAINTS: Must work on low-end Android devices, must degrade gracefully with no signal.
```

The system responds:

```
Understood. 9 critical unknowns identified.
  4 can be researched autonomously (offline payment protocols, NFC vs QR reliability
    on low-end Android, existing Nigerian offline-payment precedents, data-sync
    conflict strategies).
  3 require your decisions (settlement timing, fraud-tolerance threshold, hardware
    assumption — NFC-capable phones vs QR-only fallback).
  2 require experimentation (tap latency on your actual target devices, sync
    behavior under real network dropout).

Before execution: 3 architectural decisions needed. [presented as A/B/C, per Section 7]
```

You decide. The system then decomposes: workstreams for offline transaction queuing, conflict-resolution sync logic, driver-side reconciliation, and a fraud/abuse review layer — each broken into tasks with acceptance criteria, dependency-graphed (sync logic can't be tested until the queuing model is decided, but the reconciliation UI can be built in parallel), assigned to Developer/Tester/Security-reviewer/Adversarial-worker roles, and tracked against the approval thresholds from Section 17 (code generation autonomous, production deploy requires your approval).

This is the same shape whether the objective is a payment feature, a NEXA service-matching flow, or something with no code in it at all.

---

## What This Document Is — and Isn't

This is the **destination architecture** — the operating procedure for the system, independent of which models or frameworks implement it. It deliberately does not answer *"which agent framework, which vector database, which hosting provider."* Those choices are covered separately, mapped to a buildable stack and a project ladder that gets you here incrementally (see the companion *AI-Native Operator Field Manual*: Parts III, V, VII, and IX map almost directly onto Layers 2–3 and the Infrastructure tier above).

The order of operations, deliberately: **build the small pieces from the Field Manual's project ladder first — a working RAG memory layer, one tool-using agent, one verified coding-agent workflow — and this blueprint becomes the document that tells you how to wire those pieces together into something that runs a whole project, not just a task.**
