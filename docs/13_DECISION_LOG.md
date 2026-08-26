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
