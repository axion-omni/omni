# The AI Mastery Roadmap
### The Learning Operating System Behind the Execution Engine

The *AI Project Execution Engine* is the destination. This document is how you become capable of building it — not a list of 100 courses, but a **learning operating system**.

**The rule underneath everything else:**

> Never learn an AI technology without immediately attaching it to a real project. Learn APIs? Use one. Learn RAG? Feed it your own documents. Learn agents? Make one do a real task. Learn orchestration? Make agents collaborate on something that matters.

And don't wait until the roadmap is finished to start building. Start a crude version of the Execution Engine almost immediately — every layer below is another organ you install into a machine that's already running, not a prerequisite you clear before it's allowed to exist.

The loop, at every layer: **learn → build → use → hit a limitation → learn the next thing.**

---

## The Progression You're Actually Chasing

Ten layers, but the real marker of progress is the question you're asking shifting underneath you:

```
"How do I ask ChatGPT to do this?"
        ↓
"How do I make an AI do this through an API?"
        ↓
"How do I give the AI the information it needs?"
        ↓
"How do I give it tools?"
        ↓
"How do I make it execute multi-step tasks?"
        ↓
"How do I make multiple agents collaborate?"
        ↓
"How do I make the system verify itself?"
        ↓
"How do I make it operate continuously?"
        ↓
"How do I describe an objective and let my AI infrastructure
 figure out the execution?"
```

That last question is the Project Execution Engine. Everything below is how you earn the right to ask it.

---

## Layer 0 — AI Fundamentals & Model Literacy
**Target: 1–2 weeks**

You need to understand what you're actually commanding before you command it.

**Learn:** LLMs and tokens · context windows · system/user instructions · prompting basics · temperature · structured output · hallucinations · reasoning vs. generation · multimodal models · model strengths/weaknesses · latency · inference cost · API pricing

**Build — the Model Comparison Bench:** take one real task and run it through several models (Claude, ChatGPT, Gemini, and at least one open-weight model like DeepSeek or Qwen). Score each on accuracy, reasoning, coding, research quality, instruction-following, and cost.

**What shifts:** "which AI is smartest" stops being the question. "Which model is appropriate for this task" replaces it — this is the first seed of the model-routing instinct you'll need at Layer 9.

---

## Layer 1 — Prompt Engineering
**Target: 1–2 weeks**

Don't spend months chasing "magic prompts" — the leverage here is smaller and faster to reach than it looks.

**Learn:** role/context framing · constraints · examples (few-shot) · decomposition · structured outputs (XML/JSON schemas) · critique-and-refine loops · task-specific system prompts · prompt chaining · prompt evaluation

**Build — the Prompt Laboratory:** one task, several candidate prompts, evaluate the outputs against each other. Turn the winners into reusable templates for the roles you'll need later: Research, Planning, Coding, Analysis, Criticism, Testing, Decision-making, Documentation.

This is the primitive version of your future AI workforce — each template is a worker role waiting for a harness.

---

## Layer 2 — Programming Fundamentals
**Target: 1–2 months initially, then continuous**

This is where you become dangerous. Your existing engineering background is a real head start here, not a nice-to-have.

**Python:** variables, functions, classes, modules, files, exceptions, JSON, HTTP requests, async programming, packages, virtual environments

**JavaScript / TypeScript:** Node.js, APIs, HTTP, REST, authentication, JSON, webhooks — you already touch web development, so this is reinforcement more than new ground

**Git:** clone, branch, commit, merge, pull, push, rebase, diff, checkout

You don't need to become a computer-science professor. You need to become capable of **reading, modifying, debugging, and orchestrating** software — including software an AI wrote, which is a different and more important skill than writing it from scratch.

---

## Layer 3 — APIs
**Target: 1–3 weeks**

This is the moment AI stops being a chatbot and becomes infrastructure.

**Learn:** HTTP · REST verbs (GET/POST/PUT/PATCH/DELETE) · headers · authentication · API keys · JSON · webhooks · rate limits · streaming — then start calling Anthropic, OpenAI, Google, and other providers directly from your own code.

**Build, in order:**
1. `Your program → Model API → AI response → Your application` — the first program that calls a model without a chat window in between.
2. `Your program → Multiple AI APIs → Compare outputs → Select best response` — the first taste of routing.

Once this works, you're using AI as infrastructure, not visiting a website.

---

## Layer 4 — Databases + RAG
**Target: 2–4 weeks**

Now give the AI access to knowledge that outlives a single conversation.

**SQL / PostgreSQL:** tables, relationships, indexes, queries, transactions

**Embeddings:** the core idea — text becomes a numerical representation, and similarity search replaces keyword search

**RAG pipeline:**
```
Documents → Chunking → Embeddings → Vector database →
Retrieve relevant information → LLM → Answer
```

**Build — Your Personal Knowledge AI:** load it with your actual project documents, technical notes, research, PDFs, and specs. Ask it a real question — *"What did I decide about C-Transit's offline architecture?"* — and it should retrieve the right answer from what you actually decided, not reconstruct a plausible-sounding guess.

This is the moment the system stops being stateless and starts having institutional memory — the direct implementation of the Project Constitution and Project Memory sections in the Execution Engine document.

---

## Layer 5 — Tool Calling
**Target: 1–2 weeks**

One of the most important transitions in the whole roadmap.

```
Before: "AI, tell me today's weather."  →  it guesses or refuses.

After:  AI decides it needs weather → calls a weather tool →
        receives real data → reasons about it → responds.
```

**Learn:** function calling · schemas · tool definitions · tool permissions · structured outputs · API integrations

**Build tools like:** `search_web()` · `read_database()` · `create_task()` · `send_email()` · `calculate()` · `search_files()` · `create_report()`

Once a model can call tools, it can *do* things, not just describe them — this is the prerequisite for every Worker role in the Execution Engine.

---

## Layer 6 — Agents
**Target: 1–2 months**

The territory the final system actually requires. Don't start with a framework — understand the primitive loop first, by hand:

```
Goal → Think → Choose tool → Execute → Observe result →
Think again → Continue → Finish
```

**Learn:** agent loops · planning · tool use · memory · state · reflection · delegation · multi-agent systems · retries · error handling · human-in-the-loop · agent evaluation

**Build — a real, small agent.** Objective: *"Research the three cheapest cloud databases and produce a comparison."* It should search, collect information, compare, produce a report, and cite sources — end to end, unattended. Then extend it to use multiple tools in the same run.

This is the first working instance of a Worker from the Execution Engine — the Researcher role, built from scratch instead of assumed.

---

## Layer 7 — Agent Orchestration

Now you're building the company, not just the workers.

**Learn:** workflows · DAGs · task queues · state machines · orchestration · parallel execution · dependencies · agent handoffs · event-driven systems

```
                    ORCHESTRATOR
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                 ↓
   Researcher        Developer          Analyst
        ↓                ↓                 ↓
        └────────────────┼─────────────────┘
                         ↓
                      Tester
                         ↓
                     Reviewer
                         ↓
                       HUMAN
```

This is the Orchestrator + Workforce layers of the Execution Engine, becoming a real running system for the first time rather than a diagram.

---

## Layer 8 — Computer Use & Automation
**Target: 1–2 months**

**Learn:** browser automation · Playwright · browser agents · computer-use models · desktop automation · accessibility APIs · webhooks · scheduled jobs · event-driven automation

**Build — an AI Research Assistant:** give it an objective; it searches, opens sources, extracts information, stores findings, synthesizes, and produces a report — without you clicking through the sources yourself.

**Then build — an AI Sales/Ops Copilot:** it observes a conversation or ticket, retrieves the relevant customer/product context, proposes a response, and — only once you trust it — performs the approved action itself.

---

## Layer 9 — AI Engineering

This is where you stop using models and start building systems that don't fall over.

**Evaluation** — how do you actually know the output is good, not just plausible?
**Observability** — what happened inside the system when something went wrong?
**Prompt/version management** — which prompt version produced which result?
**Cost management** — what does each task actually cost, per run?
**Model routing** — cheap model for simple tasks, powerful model for hard ones, decided automatically
**Security** — secrets management, permissions, prompt injection, data leakage, authentication, authorization, sandboxing
**Reliability** — retries, fallbacks, validation, structured outputs, monitoring

This layer is the entire difference between an AI demo and AI infrastructure — and it's the layer most people skip, because a demo looks finished long before it's actually reliable.

---

## Layer 10 — Your AI Operating System

Everything converges here:

```
                          YOU
                           │
                     PROJECT BRIEF
                           ↓
                    ┌─────────────┐
                    │ ORCHESTRATOR│
                    └──────┬──────┘
                           ↓
                    PROJECT MEMORY
                           ↓
          ┌────────────────┼────────────────┐
          ↓                ↓                 ↓
      Research         Planning          Architecture
          ↓                ↓                 ↓
          └────────────────┼─────────────────┘
                           ↓
                       EXECUTION
                           ↓
          ┌────────────────┼────────────────┐
          ↓                ↓                 ↓
       Coding          Marketing          Engineering
          ↓                ↓                 ↓
          └────────────────┼─────────────────┘
                           ↓
                        TESTING
                           ↓
                       CRITIC AI
                           ↓
                    HUMAN DECISION
                           ↓
                      DEPLOYMENT
                           ↓
                      MONITORING
                           ↓
                       LEARNING
```

This is the destination — the same diagram, now buildable, because every box has a layer above it that taught you how to construct it.

---

## What to Actually Study — Four Sources, Used Together

Don't collect courses like Pokémon. Run these four in parallel, weighted toward the bottom two as you progress.

**1. Official documentation** — your primary source once you're building: Anthropic docs, OpenAI docs, Google AI docs, GitHub docs, PostgreSQL docs, Python docs, TypeScript docs, Playwright docs. Documentation teaches you how the machinery actually works, not how a course author simplified it.

**2. Structured courses** — for conceptual foundations only, not completion badges: DeepLearning.AI, freeCodeCamp, CS50, fast.ai. Take the module that fills the specific gap you currently have. Skip the rest.

**3. Projects** — the most important source. Every concept earns a build:

| Learn | Build |
|---|---|
| APIs | AI API client |
| Prompting | Prompt laboratory |
| RAG | Personal knowledge AI |
| Tool calling | AI calculator/researcher |
| Agents | Autonomous researcher |
| Automation | Browser research agent |
| Orchestration | Multi-agent project manager |
| Evaluation | AI testing system |
| Memory | Persistent project assistant |
| Everything | Project Execution Engine |

**4. Your own problems — the actual secret weapon.** Stop inventing toy problems once you have real ones. You already have C-Transit, NEXA, and whatever comes after them — those are your laboratories, not hypothetical case studies. A RAG system that actually answers "what did I decide about C-Transit's offline architecture" teaches you more in an afternoon than a generic tutorial teaches in a week, because you'll immediately notice when it's wrong.

---

## The Hard Rule

> Never learn an AI technology without immediately attaching it to a real project.

- Learn APIs? Use one, today, on something real.
- Learn RAG? Point it at your actual documents, not a sample dataset.
- Learn agents? Make one perform a task you'd otherwise do yourself.
- Learn orchestration? Make two agents actually hand work to each other.
- Learn automation? Automate something you currently do by hand.
- Learn evaluation? Measure — with numbers — whether your system actually works, not whether it feels like it does.

---

## And Don't Follow It Linearly

You will jump ahead constantly, and that's correct, not a failure of discipline. You'll be deep in Layer 3 (APIs) and suddenly need Layer 4 (RAG) because the project demands it. Go learn just enough RAG to solve that problem, then come back. **The roadmap is a map, not a prison** — the loop that matters is *learn → build → use → hit a limitation → learn the next thing*, and limitations don't arrive in the order a syllabus would prefer.

---

## How This Connects to the Other Two Documents

- The **AI-Native Operator Field Manual** is the wide view — the full ecosystem, the ladder, the economics, the businesses this unlocks.
- The **Project Execution Engine** is the destination architecture — what the finished system does once it exists.
- **This roadmap** is the only one of the three that tells you what to do on Monday morning: start Layer 0 this week, and don't wait for Layer 10 to start assembling a crude version of the Engine. The first ugly version can exist by the end of Layer 6 — a single agent that researches, decides, and reports, with you approving the risky steps. Layers 7–10 don't replace it; they make it reliable enough to trust with something that matters.
