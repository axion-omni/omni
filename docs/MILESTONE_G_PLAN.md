# Milestone G — Tool system (sandboxed) (Deterministic Build Spec)

> **How to use this file.** Sessions top to bottom; each a brick (implement →
> L2 test → operator L3 → update the six docs + progress.json → commit). Labels
> G1… map to the next global `S<n>`. Code + CONTRACTS win. Grounded in:
> destination §8 (agents/tools), §11 (permissions, untrusted tool output);
> Construction Spec Part V (Stage 5), Part XIII (tools), Part XX (security).

> **Capability after this milestone:** an agent-initiated tool call (web search,
> file read, one external API) executes inside a worker and its result flows back.
> This is the substrate agents (H) act through.

## Definition of done (authoritative gate)
Destination §15 Milestone G: **“An agent-initiated tool call executes in a worker,
result reaches the phone.”** Construction Spec Stage 5: “An LLM call requests a
tool, the tool executes, the result returns to the model.” Verified L3.

## Prerequisites
- **Milestones E + F at L3** (memory + workers; tools run inside worker jobs).
- **Operator prep:** any external-tool API keys (e.g. a web-search API) as secrets.

## New dependencies / config / secrets
- Per-tool as needed (e.g. a search API client via `requests`). Config:
  `TOOLS_ENABLED` (allowlist), per-tool keys.

## Contracts introduced (add to CONTRACTS.md as built)
- `core/tools/base.py`: `class Tool(ABC)` with `name: str`,
  `permission_tier: str` (`read|write|external|dangerous`),
  `input_schema` (Pydantic model), `execute(input) -> ToolResult`.
- `core/tools/registry.py`: `get_tool(name)`, `available_tools(settings)`
  (respects `TOOLS_ENABLED`) — mirrors the model registry pattern.
- `ToolResult` (`ok`, `output`, `error`, `evidence/source`).

## Likely decisions to log (DECISIONS.md)
- **D0xx — permission tiers** and where they’re enforced (server-side, before
  execute), never trusting the model’s claim.
- **D0xx — tool output is untrusted data** (Part XX): results are quoted to the
  model as data, never concatenated as instructions.
- **D0xx — sandboxing level** for this milestone (in-worker, no shell/network
  beyond declared tools; filesystem tool confined to a project workspace dir).

## Sessions

### Session G1 — Tool interface + tool registry
- **Files:** `core/tools/base.py`, `core/tools/registry.py`, `core/tools/
  exceptions.py`; `tests/test_tool_registry.py`.
- **Test gate (L2):** a fake `Tool` registers and resolves; unknown tool raises a
  clear error; `available_tools` respects the allowlist; input validated by schema.
- **Commit:** `feat: Session <n> - Tool interface + registry (Milestone G)`.

### Session G2 — First tools: web_search, read_file
- **Files:** `core/tools/web_search.py` (external tier, `requests`, injectable
  http), `core/tools/read_file.py` (read tier, confined to a workspace root);
  `tests/test_tools_builtin.py`.
- **Test gate (L2):** web_search parses a faked API response into `ToolResult`;
  read_file refuses paths outside the workspace root (path-traversal test); no
  network.
- **Operator L3:** real search key → a real query returns results.
- **Commit:** `feat: Session <n> - web_search + read_file tools`.

### Session G3 — Tool-call loop (model requests a tool)
- **Files:** `core/tools/loop.py` — given a model response requesting a tool
  (structured), enforce permission tier, execute, feed the result back as data,
  and continue until a final answer; `tests/test_tool_loop.py`.
- **Test gate (L2):** a scripted fake model requests a tool once then answers;
  the loop executes the tool and returns the final answer; a disallowed tier is
  blocked; a tool error is surfaced, not crashed on.
- **Operator L3:** local: a prompt that needs search produces a tool-assisted answer.
- **Commit:** `feat: Session <n> - tool-call loop with permission enforcement`.

### Session G4 — Run tools inside a worker job + phone result
- **Files:** a job handler `tool_task` (Milestone F registry) that runs the loop;
  `tests/test_worker_tools.py`.
- **Test gate (L2):** a `tool_task` job runs the loop (faked tool+model) and
  completes with the result; result delivery to Telegram faked.
- **Operator L3 — THE GATE:** from the phone, a request that triggers a tool →
  the tool runs in the worker and the result returns. Milestone G done.
- **Commit:** `feat: Session <n> - agent-initiated tool call in a worker (Milestone G done)`.

## Security / deploy-safety notes
- **Permission tiers enforced server-side**, before `execute`; `dangerous`/`write`
  tiers require an approval gate later (J).
- **Prompt-injection**: a required test feeds a malicious instruction inside a
  tool result and asserts it is not executed as a command.
- Filesystem/network access confined to declared tools + a project workspace.

## Explicitly deferred
- Multi-tool agents with planning → H/I. Browser/computer control → post-MVP
  (Stage 12). Human approval for dangerous tools → **Milestone J**.
