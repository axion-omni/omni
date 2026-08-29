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
apps/
└── cli/
    └── main.py                        Thin terminal interface. Reads argv
                                         (incl. optional --model <logical>),
                                         resolves via the registry, prints
                                         output. No logic beyond that here.
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

There is no memory layer, no tools, and no agents yet — those are Sessions 6+
(see ROADMAP.md and BUILD_PLAN.md). Model routing is now complete: routing
(Session 4) maps a (task_type, MODEL_POLICY) pair to a logical name and logs
the decision; the registry resolves that name to a concrete (provider,
model_id); retry (Session 5) wraps the call with capped exponential backoff for
retryable errors only and one configured fallback. Today every logical name
resolves to the active provider's single default model (D007), so flipping
`MODEL_POLICY` changes the logical selection + logged decision for an identical
prompt, and the fallback becomes meaningful once a second model is registered
(D008). `core/models/factory.py` remains the single place that selects a
provider from `ACTIVE_PROVIDER`. Nothing in this repo should be assumed to exist
beyond what's listed above without checking.

## Rule enforced by this structure

No file outside `core/models/providers/` imports a provider SDK directly.
This is what lets a second provider be added later as a new file + a
registry entry (once the registry exists), not a rewrite of callers.

## Last verified against actual code
Commit `3e3b63e` + Session 5 (retry + fallback). `pytest -v` → 46 passed in the
assistant sandbox (Level 2). If this file and the actual `core/` tree
disagree, the code wins — flag it, don't silently trust this doc.
