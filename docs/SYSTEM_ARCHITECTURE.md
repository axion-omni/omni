# System Architecture

This describes what **actually exists in this repository right now**. For the
full destination architecture (the eventual system), see
`PERSONAL_AI_OS_MASTER_ARCHITECTURE.md` (the current destination per D006;
`docs/00_MASTER_ARCHITECTURE.md` is the pointer to it) — that is the target,
not the current state. Do not assume anything described there is built until
it appears here.

## As-built (current)

```
core/
├── config.py                          Settings loader (env vars only)
└── models/
    ├── base.py                        ModelProvider ABC, ModelResponse,
    │                                   ModelCapabilities — see CONTRACTS.md
    ├── exceptions.py                  Shared exception hierarchy (incl.
    │                                   ModelNotRegisteredError, added S3)
    ├── factory.py                     Provider selector — reads ACTIVE_PROVIDER
    │                                   and constructs the matching provider.
    │                                   Now the registry's construction
    │                                   primitive, not caller-facing (D007).
    ├── registry.py                    Model Registry (Session 3). Maps logical
    │                                   names ("reasoning-strong", "coding",
    │                                   "cheap-fast") -> (provider, model_id).
    │                                   Caller-facing resolution layer + a pure
    │                                   estimated_cost() helper.
    ├── routing.py                     Policy routing (Session 4). route(
    │                                   task_type, MODEL_POLICY) -> logical name
    │                                   the registry resolves; logs the decision.
    ├── retry.py                       Retry + fallback (Session 5). Backoff on
    │                                   retryable errors only; one fallback
    │                                   logical model. sleep injectable.
    └── providers/
        ├── anthropic_provider.py      Only file that imports the `anthropic`
        │                               SDK. Implements ModelProvider.
        └── openrouter_provider.py     Only file that talks to OpenRouter's
                                         REST API. Implements ModelProvider.
                                         Added for dev/testing without
                                         Anthropic credits — unchanged
                                         Anthropic path stays fully intact.
core/
└── memory/                            Persistence layer (Milestone C, Session 6+).
    ├── exceptions.py                  MemoryError hierarchy (Not-configured,
    │                                   Connection) — mirrors the model layer.
    └── db.py                          DB access seam. Only file that imports the
                                         Postgres driver (lazy). connect()/ping()
                                         over DATABASE_URL; connector injectable.
                                         No schema yet (schema = Session 7).
apps/
└── cli/
    └── main.py                        Thin terminal interface. Reads argv
                                         (incl. optional --model <logical>),
                                         resolves via the registry, prints
                                         output. No logic beyond that here.
infra/
└── docker-compose.yml                 Local dev Postgres (pgvector image).
                                         Dev convenience only; prod uses managed
                                         Postgres with the URL in the host secret
                                         manager.
```

**How components interact today:**

```
python apps/cli/main.py "<prompt>" [--model <logical-name>]
    → core.config.load_settings() → Settings
    → (if no --model) core.models.routing.route("general", settings.model_policy)
        → logical name   [logs the routing decision]
    → core.models.registry.build_default_registry(settings) → ModelRegistry
        (internally: core.models.factory.get_active_provider(settings))
    → core.models.retry.generate_with_retry(registry, prompt,
        primary=logical_name, fallback=settings.model_fallback or None)
        → registry.resolve(logical_name) → (ModelProvider, model_id)
        → provider.generate(prompt, model=model_id) under capped backoff;
          retryable errors retried, one fallback model tried if primary exhausts
        → ModelResponse
    → printed to stdout (text) / stderr (usage + selection + errors)
```

The **memory layer exists only as a connection seam** (`core/memory/db.py`,
Session 6): it can connect to Postgres and health-check it, but there is **no
schema, no Constitution, and no persistence yet** — the chat path above does not
touch it. Schema is Session 7, the Constitution repository Session 8, CLI
persistence Session 9 (see MILESTONE_C_PLAN.md). There are still no tools and no
agents. Model routing is complete: routing (Session 4) maps a (task_type,
MODEL_POLICY) pair to a logical name and logs the decision; the registry
resolves that name to a concrete (provider, model_id); retry (Session 5) wraps
the call with capped exponential backoff for retryable errors only and one
configured fallback. Today every logical name resolves to the active provider's
single default model (D007), so flipping `MODEL_POLICY` changes the logical
selection + logged decision for an identical prompt, and the fallback becomes
meaningful once a second model is registered (D008). `core/models/factory.py`
remains the single place that selects a provider from `ACTIVE_PROVIDER`. Nothing
in this repo should be assumed to exist beyond what's listed above without
checking.

## Rule enforced by this structure

No file outside `core/models/providers/` imports a provider SDK directly, and
no file outside `core/memory/` imports the database driver directly (D002,
generalized to storage in D009). This is what lets a provider or a storage
backend be swapped as a localized change, not a rewrite of callers.

## Last verified against actual code
Commit `ceaa514` + Session 6 (DB access seam). `pytest -v` → 53 passed, 1
skipped (the live DB ping, skipped without DATABASE_URL) in the assistant
sandbox (Level 2). If this file and the actual `core/` tree disagree, the code
wins — flag it, don't silently trust this doc.
