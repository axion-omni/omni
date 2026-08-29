# Contracts

Interfaces, schemas, and agreements between components. If code and this
file disagree, **the code is correct and this file is stale** — fix the
file, don't trust it blindly.

## `ModelProvider` (core/models/base.py)

Every model provider must implement:

```python
class ModelProvider(ABC):
    name: str

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        model: str | None = None,
    ) -> ModelResponse:
        ...

    def capabilities(self, model: str | None = None) -> ModelCapabilities:
        ...
```

**Agreement:** `generate()` must never let a raw SDK exception escape — it
must raise a subclass of `core.models.exceptions.ModelError` (see below).
This is what lets any caller catch one exception type regardless of provider.

## `ModelResponse` (core/models/base.py)

```python
@dataclass
class ModelResponse:
    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    raw: Any = None   # original SDK object — for debugging only, never
                       # depended on by calling code
```

`raw` is explicitly exempt from the "uniform shape" guarantee. Nothing
outside a provider file should ever read `.raw`.

## `ModelCapabilities` (core/models/base.py)

```python
@dataclass
class ModelCapabilities:
    supports_tool_calling: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    max_context_tokens: int = 0
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0
```

Consumed by the router once it exists (Session 3+). Not consumed by
anything yet.

## Exception hierarchy (core/models/exceptions.py)

```
ModelError
├── ModelAuthError            bad/missing credentials
├── ModelRateLimitError       retryable — caller may back off and retry
├── ModelTimeoutError         retryable
├── ModelUnavailableError     retryable — provider down/overloaded
└── ModelInvalidRequestError  NOT retryable — our request was malformed
```

**Agreement for future retry logic (Session 5+):** only `RateLimitError`,
`TimeoutError`, and `UnavailableError` are safe to retry automatically.
`AuthError` and `InvalidRequestError` must fail fast — retrying them wastes
calls and money without any chance of succeeding.

## `Settings` (core/config.py)

```python
@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    model_policy: str        # "free" | "cheap" | "balanced" | "quality" | "maximum"
    active_provider: str     # "anthropic" | "openrouter"
    openrouter_api_key: str
    openrouter_model: str
```

Sourced only from environment variables (`.env` locally). No component
outside `core/config.py` should call `os.environ` directly — route new
config through `Settings`.

## `get_active_provider(settings)` (core/models/factory.py)

```python
def get_active_provider(settings: Settings) -> ModelProvider:
    ...
```

**Agreement:** this is the only place that decides *which* `ModelProvider`
implementation a caller gets. Nothing else should construct
`AnthropicProvider` or `OpenRouterProvider` directly except tests and this
function. Defaults to Anthropic — switching requires only
`ACTIVE_PROVIDER=openrouter` in `.env`.

**Explicitly temporary:** this function has none of the capability-matching
or cost-awareness the real Model Registry (Session 3) will have. When
Session 3 lands, callers should migrate to the registry; this file is
expected to shrink to a thin wrapper or be removed. Not a breaking change
either way, since it returns the same `ModelProvider` type either function
would.

## `OpenRouterProvider` (core/models/providers/openrouter_provider.py)

Implements `ModelProvider` exactly like `AnthropicProvider` does. Talks to
OpenRouter's OpenAI-compatible REST endpoint via `requests` (no SDK
dependency added). Default model: `meta-llama/llama-3.3-70b-instruct:free`
— overridable via `OPENROUTER_MODEL`, since free-tier model slugs on
OpenRouter rotate over time.

## Not yet defined (will be added here when built)

- Full Model Registry with capability/cost-based routing — Session 3
- Tool interface (`core.tools.Tool`) — Session ~9+
- Agent contract (task/output shape every agent returns) — Session ~11+
- Task graph node schema — Session ~13+
- Project Constitution schema — Session ~6+ (Stage 3)
