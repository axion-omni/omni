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
├── ModelInvalidRequestError  NOT retryable — our request was malformed
└── ModelNotRegisteredError   NOT retryable — unknown logical model name
                              (raised by the registry; added Session 3)
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
    model_fallback: str      # logical name tried once if primary exhausts retries; "" = none
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
implementation gets constructed from `Settings`. Nothing else should construct
`AnthropicProvider` or `OpenRouterProvider` directly except tests, this
function, and `registry.build_default_registry()` (which calls it). Defaults to
Anthropic — switching requires only `ACTIVE_PROVIDER=openrouter` in `.env`.

**Role after Session 3 (see D007):** narrowed from caller-facing to the
registry's provider-construction primitive. Callers now resolve models through
`ModelRegistry`, not by calling this directly. The function was retained (not
deleted) so provider selection + key handling stay in one place; its signature
and behavior are unchanged.

## `ModelRegistry` (core/models/registry.py) — Session 3

```python
class ModelRegistry:
    def register(self, logical_name: str, provider: ModelProvider, model_id: str) -> None: ...
    def resolve(self, logical_name: str) -> tuple[ModelProvider, str]: ...
    def capabilities(self, logical_name: str) -> ModelCapabilities: ...
    def list_models(self) -> list[str]: ...
    def __contains__(self, logical_name) -> bool: ...

def build_default_registry(settings: Settings) -> ModelRegistry: ...
def estimated_cost(capabilities: ModelCapabilities, response: ModelResponse) -> float: ...

DEFAULT_LOGICAL_MODEL = "reasoning-strong"
LOGICAL_MODEL_NAMES = ("reasoning-strong", "coding", "cheap-fast")
```

**Agreements:**
- `resolve()` returns a `(provider, model_id)` pair. Callers pass `model_id`
  straight into `provider.generate(prompt, model=model_id)`. Above this layer,
  **no caller writes a concrete model string or a provider name** — they use a
  logical name only. This is the lock-in control from Master Construction
  Spec Part V/XXII, now enforced in code.
- An unknown logical name raises **`ModelNotRegisteredError`** (a `ModelError`),
  never a bare `KeyError`. One catch type for callers, same as every other
  model-layer failure.
- `capabilities(logical_name)` is **sourced from the provider**
  (`ModelProvider.capabilities(model_id)`), not stored a second time in the
  registry. The registry is where capability/cost data is *queried from*
  (destination Section 9), not a duplicate source of truth.
- `build_default_registry(settings)` reuses `factory.get_active_provider()`, so
  `ACTIVE_PROVIDER` selection and key handling are not duplicated, and D004's
  no-Anthropic-credit dev route is preserved. It registers the active provider
  under every logical name today (one real model per provider); Session 4's
  routing table is what makes the names diverge.
- `estimated_cost()` is pure (no I/O): `tokens ÷ 1e6 × per-million rate`, summed
  over input+output. It is the per-call building block for cost-to-date
  reporting (destination Sections 9/13; Spec Part XIX); the running per-project
  total is the event log's job later (Stage 16), not this function's.

**Explicitly deferred:** retry + fallback is Session 5
(`core/models/retry.py`). The registry is the seam it builds on.

## `route()` (core/models/routing.py) — Session 4

```python
POLICIES = ("free", "cheap", "balanced", "quality", "maximum")
DEFAULT_TASK_TYPE = "general"

def route(task_type: str, policy: str) -> str: ...   # -> a logical model name
```

**Agreements:**
- `route()` maps a `(task_type, policy)` pair to a **logical model name** that
  the registry then resolves. Callers above this layer pass a task type + the
  `MODEL_POLICY` from `Settings.model_policy` — never a model or provider name.
- Every name the routing table can emit is a registered `LOGICAL_MODEL_NAME`
  (validated at import; a bad table raises `ValueError` at import, not a
  runtime `ModelNotRegisteredError`).
- `route()` **never raises**: an unknown `task_type` falls back to the
  `general` row, an unknown `policy` falls back to `DEFAULT_LOGICAL_MODEL`.
- Every call logs the decision to the `core.models.routing` logger
  (`routing decision: task_type=… policy=… -> logical_model=…`). That log line
  is the observability hook (Spec Part XVIII) and the level-3 proof that
  flipping `MODEL_POLICY` changed the selection.
- Today all logical names resolve to one concrete model per provider (D007), so
  routing changes the logical selection + log line but not yet the concrete
  model; physical differentiation lands when a second model is registered.

## retry + fallback (core/models/retry.py) — Session 5

```python
RETRYABLE_ERRORS = (ModelRateLimitError, ModelTimeoutError, ModelUnavailableError)

def call_with_retry(fn, *, max_attempts=3, base_delay=1.0, sleep=time.sleep) -> T: ...

def generate_with_retry(
    registry, prompt, *, primary, fallback=None,
    max_attempts=3, base_delay=1.0, sleep=time.sleep, **generate_kwargs,
) -> ModelResponse: ...
```

**Agreements:**
- Only `RETRYABLE_ERRORS` are retried (exponential backoff `base_delay*2**n`:
  1s, 2s, 4s…). `ModelAuthError`, `ModelInvalidRequestError`, and
  `ModelNotRegisteredError` **fail fast** — no retry.
- Exhausting `max_attempts` re-raises the **original** exception, never a
  wrapped one. `max_attempts` counts the first try (3 ⇒ at most 2 retries).
- `generate_with_retry` resolves `primary` via the registry and generates under
  retry; only if that exhausts retries on a **retryable** error does it try
  `fallback` **once**. A non-retryable failure never triggers the fallback.
  `fallback=None` or `fallback == primary` ⇒ no fallback.
- `sleep` is injectable so tests exercise backoff with no real delay.
- Per D008: the fallback only changes the outcome once it resolves to a
  different provider/model than the primary (needs a second registered model).

## `OpenRouterProvider` (core/models/providers/openrouter_provider.py)

Implements `ModelProvider` exactly like `AnthropicProvider` does. Talks to
OpenRouter's OpenAI-compatible REST endpoint via `requests` (no SDK
dependency added). Default model: `meta-llama/llama-3.3-70b-instruct:free`
— overridable via `OPENROUTER_MODEL`, since free-tier model slugs on
OpenRouter rotate over time.

## Not yet defined (will be added here when built)

- Tool interface (`core.tools.Tool`) — Session ~9+
- Agent contract (task/output shape every agent returns) — Session ~11+
- Task graph node schema — Session ~13+
- Project Constitution schema — Session ~6+ (Stage 3)
