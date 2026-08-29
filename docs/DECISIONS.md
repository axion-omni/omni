# Decision Log

Append-only. Never edit a past entry — if a decision is reversed, add a new
entry that references the old one.

---

### D001 — Language: Python for the engine core
**Date:** Session 1
**Decision:** Python 3.12 for `core/`, `agents/`, `tools/`, orchestrator.
**Why:** The AI-systems ecosystem (agent frameworks, RAG libraries, provider
SDKs, eval tooling) is deepest in Python. Go and Dart remain the right
choice for C-Transit/NEXA's own product surfaces, not for this engine.
**Alternative considered:** TypeScript/Node — rejected only for the core
engine because the agent-framework ecosystem (LangGraph, CrewAI-equivalents)
is thinner there today. Revisit if a future UI layer wants a Node backend —
that's a separate service, not a rewrite of this one (see D003).
**Reversible:** Yes, if provider abstraction (D002) is respected, swapping
the orchestrator language later doesn't require rewriting provider code.

### D002 — Provider abstraction boundary
**Date:** Session 1
**Decision:** No file outside `core/models/providers/` may import a
provider SDK directly. All access goes through `ModelProvider`.
**Why:** This is the single control that prevents permanent lock-in to
Anthropic specifically — a new provider is a new file implementing the
interface, not a rewrite.
**Reversible:** N/A — this is a standing rule, not a one-time choice.

### D003 — Core engine stays headless
**Date:** Session 1 (documented in advance, enforced starting Stage 15/UI)
**Decision:** The engine exposes itself over an API from the start. No UI
framework gets imported into `core/`.
**Why:** Part XV of the master architecture requires the same underlying
system to be reachable from PC, phone, browser, and Telegram without
duplicated logic. Retrofitting this later is expensive; it's nearly free
if respected from Session 1 onward.

### D004 — OpenRouter added as a second provider, ahead of the Session 3 registry
**Date:** post-Session 1, pre-Session 2
**Decision:** Added `OpenRouterProvider` (implements the existing
`ModelProvider` interface) plus a minimal `core/models/factory.py` that
switches between it and `AnthropicProvider` via one env var
(`ACTIVE_PROVIDER`). Default model: `meta-llama/llama-3.3-70b-instruct:free`.
**Why:** No Anthropic API credits currently available for local testing.
This unblocks development without waiting on funding, and without touching
the Anthropic path at all.
**What was NOT touched:** `core/models/providers/anthropic_provider.py` —
zero lines changed. `AnthropicProvider` remains the default
(`ACTIVE_PROVIDER=anthropic`) and is fully intact for when credits return.
**Scope note:** `factory.py` is intentionally minimal — a flat env-var
switch, not the capability/cost-aware Model Registry planned for Session 3
in ROADMAP.md. It exists to unblock testing today; Session 3 absorbs or
replaces it. This is a known, logged overlap, not an accidental duplication.
**Reversible:** Yes — switching back to Anthropic-only requires no code
change, just `ACTIVE_PROVIDER=anthropic` (already the default).
