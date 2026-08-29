# System Architecture

This describes what **actually exists in this repository right now**. For the
full destination architecture (the eventual system), see the companion
document `AI_Project_Execution_Engine.md` — that is the target, not the
current state. Do not assume anything described there is built until it
appears here.

## As-built (current)

```
core/
├── config.py                          Settings loader (env vars only)
└── models/
    ├── base.py                        ModelProvider ABC, ModelResponse,
    │                                   ModelCapabilities — see CONTRACTS.md
    ├── exceptions.py                  Shared exception hierarchy
    ├── factory.py                     Minimal provider switch (NOT the
    │                                   Session 3 registry — see below)
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
    └── main.py                        Thin terminal interface. Reads argv,
                                         calls core, prints output. No
                                         logic beyond that lives here.
```

**How components interact today:**

```
python apps/cli/main.py "<prompt>"
    → core.config.load_settings() → Settings
    → core.models.factory.get_active_provider(settings) → ModelProvider
    → provider.generate(prompt) → ModelResponse
    → printed to stdout (text) / stderr (usage + errors)
```

There is no full registry, no capability-based routing, no memory
layer, no tools, and no agents yet — those are Sessions 3+ (see ROADMAP.md).
`core/models/factory.py` is a deliberately minimal stand-in for the routing
piece of Session 3, added out of sequence to unblock testing while no
Anthropic credits are available — see DECISIONS.md D004. Nothing in this
repo should be assumed to exist beyond what's listed above without checking.

## Rule enforced by this structure

No file outside `core/models/providers/` imports a provider SDK directly.
This is what lets a second provider be added later as a new file + a
registry entry (once the registry exists), not a rewrite of callers.

## Last verified against actual code
Commit `5def786`. If this file and the actual `core/` tree disagree, the
code wins — flag it, don't silently trust this doc.
