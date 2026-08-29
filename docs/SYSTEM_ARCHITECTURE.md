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
    → core.models.registry.build_default_registry(settings) → ModelRegistry
        (internally: core.models.factory.get_active_provider(settings))
    → registry.resolve(logical_name) → (ModelProvider, model_id)
    → provider.generate(prompt, model=model_id) → ModelResponse
    → printed to stdout (text) / stderr (usage + errors)
```

There is no capability-based *routing table* yet (task-type + MODEL_POLICY →
logical name is Session 4), no retry/fallback (Session 5), no memory layer, no
tools, and no agents yet — those are Sessions 4+ (see ROADMAP.md and
BUILD_PLAN.md). The registry resolves logical names to a concrete
(provider, model_id) pair and exposes provider-sourced capabilities + a
per-call `estimated_cost()` helper; today every logical name resolves to the
active provider's default model (one verified model per provider), which
Session 4's routing layer differentiates once more models are registered.
`core/models/factory.py` remains the single place that selects a provider from
`ACTIVE_PROVIDER`; the registry now sits on top of it (D007). Nothing in this
repo should be assumed to exist beyond what's listed above without checking.

## Rule enforced by this structure

No file outside `core/models/providers/` imports a provider SDK directly.
This is what lets a second provider be added later as a new file + a
registry entry (once the registry exists), not a rewrite of callers.

## Last verified against actual code
Commit `13de664` + Session 3 (registry). `pytest -v` → 31 passed in the
assistant sandbox (Level 2). If this file and the actual `core/` tree
disagree, the code wins — flag it, don't silently trust this doc.
