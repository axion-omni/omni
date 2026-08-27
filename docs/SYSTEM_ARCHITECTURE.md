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
    └── providers/
        └── anthropic_provider.py      Only file that imports the `anthropic`
                                         SDK. Implements ModelProvider.
```

**How components interact today:**

```
caller → core.config.load_settings() → Settings
caller → AnthropicProvider(api_key=settings.anthropic_api_key)
caller → provider.generate(prompt, ...) → ModelResponse
```

There is no registry, no routing, no CLI, no memory layer, no tools, and no
agents yet — those are Sessions 3+ (see ROADMAP.md). Nothing in this repo
should be assumed to exist beyond what's listed above without checking.

## Rule enforced by this structure

No file outside `core/models/providers/` imports a provider SDK directly.
This is what lets a second provider be added later as a new file + a
registry entry (once the registry exists), not a rewrite of callers.

## Last verified against actual code
Commit `5def786`. If this file and the actual `core/` tree disagree, the
code wins — flag it, don't silently trust this doc.
