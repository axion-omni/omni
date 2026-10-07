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
    database_url: str = ""   # Postgres connection string; "" = no database configured
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

## Memory access seam (core/memory) — Session 6 (Milestone C)

```python
# core/memory/exceptions.py
MemoryError                     # base
├── DatabaseNotConfiguredError  # DATABASE_URL empty
└── DatabaseConnectionError     # driver/connection failure

# core/memory/db.py
def connect(settings, *, connector=None) -> connection: ...
def ping(settings, *, connector=None) -> bool: ...
```

**Agreements:**
- `core/memory/db.py` is the **only** place the Postgres driver is imported
  (lazily), just as provider SDKs live only in `core/models/providers/` (D009).
- `connect()` raises `DatabaseNotConfiguredError` when `DATABASE_URL` is empty
  and `DatabaseConnectionError` (never a raw driver exception) on failure.
- `connector` is injectable so callers/tests supply a fake connection without a
  driver or a live DB — the same injection pattern as the model providers.
- No schema or queries live here yet. The Constitution schema (Session 7) and
  repository (Session 8) build on this seam.

## Constitution schema (core/memory/models.py + infra/migrations) — Session 7

```python
class Constitution(BaseModel):   # 13 fields, AI_Project_Execution_Engine.md §2
    mission: str = ""
    purpose: str = ""
    desired_outcome: str = ""
    success_criteria: list[str] = []
    constraints: list[str] = []
    assumptions: list[str] = []
    non_negotiables: list[str] = []
    available_resources: list[str] = []
    known_facts: list[str] = []
    unknowns: list[str] = []
    risks: list[str] = []
    decisions: list[str] = []
    change_history: list[str] = []   # append-only, owned by the repository
```

Tables (`infra/migrations/0001_init.sql`): `projects(id, name, created_at)` and
`constitutions(id, project_id→projects, version, content jsonb, created_at,
unique(project_id, version))`. **Append-only + versioned + per-project scoped**
(D010).

```python
# core/memory/migrations.py — forward-only runner
def discover_migrations(dir=MIGRATIONS_DIR) -> list[Migration]: ...
def pending(migrations, applied: set[str]) -> list[Migration]: ...
def run(settings=None, *, connector=None, migrations_dir=MIGRATIONS_DIR) -> list[str]: ...
```

**Agreements:** the Constitution is stored one JSONB row per version, never
overwritten; every write appends to `change_history` and bumps `version`
(repository enforces this — Session 8). Migrations are plain SQL applied in
lexical order, tracked in `schema_migrations`, forward-only. `run()` uses the
`core/memory/db.py` seam (injectable connector).

## `OpenRouterProvider` (core/models/providers/openrouter_provider.py)

Implements `ModelProvider` exactly like `AnthropicProvider` does. Talks to
OpenRouter's OpenAI-compatible REST endpoint via `requests` (no SDK
dependency added). Default model: `meta-llama/llama-3.3-70b-instruct:free`
— overridable via `OPENROUTER_MODEL`, since free-tier model slugs on
OpenRouter rotate over time.


## `ConstitutionRepository` (core/memory/constitution.py) — Session 8

```python
class ConstitutionRepository:
    def __init__(self, settings: Settings, *, connector=None) -> None: ...

    def create(self, name: str, constitution: Constitution | None = None) -> str: ...
    def get(self, project_id: str) -> Constitution: ...
    def get_version(self, project_id: str, version: int) -> Constitution: ...
    def append_change(self, project_id: str, change: str, **field_updates) -> int: ...
    def history(self, project_id: str) -> list[tuple[int, datetime]]: ...
    ```

## CLI `constitution` subcommands (apps/cli/main.py) — Session 9
python apps/cli/main.py constitution create <name> [--mission TEXT] [--purpose TEXT] [--desired-outcome TEXT]
python apps/cli/main.py constitution show <project_id>
python apps/cli/main.py constitution amend <project_id> --change TEXT [--set KEY=VALUE]...

text

**Agreements:**
- **Dispatch:** `argv[1] == "constitution"` routes to the constitution handler;
  anything else routes to the chat handler, unchanged (Sessions 2–5). Existing
  chat tests must stay green.
- **Thin wrappers only.** Handlers parse argv, call exactly one repository
  method, format the result. No validation, business rules, or storage logic
  lives in the CLI — those belong to the repository (D003).
- **Output conventions:**
  - `create` prints **only** the generated `project_id` (uuid string) to
    stdout, so it is pipeable: `PID=$(python apps/cli/main.py constitution
    create "X")`.
  - `show` prints a human-readable block: `project_id`, `version`, then each
    Constitution field on its own line. List fields render as compact JSON
    (single line).
  - `amend` prints **only** the new version number to stdout.
- **`--set KEY=VALUE` is repeatable and value-typed.** VALUE is parsed as
  JSON when valid (so `["a","b"]` is a list, `123` is an int, `true` is a
  bool); otherwise it is a plain string. Malformed pairs (no `=`) raise a
  clean error — never a silent no-op.
- **Error handling matches the chat path.** `MemoryError` (base) is caught
  and printed as one clean line (`Error (ConstitutionNotFoundError): ...`),
  exit code 1, no traceback. `ValueError` from `--set` parsing is similarly
  caught. Anything else is a bug and propagates.
- **Injection:** `run()` accepts an optional `repo_builder` parameter
  (default: constructs a real `ConstitutionRepository(settings)`) — same
  pattern as the existing `registry_builder` / `settings_loader`. Tests
  inject a fake; production uses the default.
- **argparse** is used for the constitution subcommand tree only. The chat
  path keeps its hand-parse (see `_parse_chat_args` docstring for why).



## Cloud API surface (apps/api/) — Session 10 (Milestone D, D1)

```python
# apps/api/settings.py
@dataclass(frozen=True)
class ApiSettings:
    engine: Settings          # core.config.Settings — the engine's settings

def load_api_settings() -> ApiSettings: ...

# apps/api/app.py
def create_app(settings: ApiSettings) -> FastAPI: ...
app = create_app(load_api_settings())   # uvicorn entry point
Endpoints (D1):

GET /health → 200 {"status": "ok"}. The deploy health check; Render
polls it, and the operator uses it to confirm a running instance.

Agreements:

The API is a thin interface (D003, D014). No business logic lives in
apps/api/ beyond wiring HTTP to core/. Any future handler parses the
request, calls one engine entry point, formats the response — nothing more.

create_app takes settings explicitly (factory pattern) so tests construct
the app against fakes with no env, no network, no keys — same discipline as
apps/cli/main.py.

Settings are stored on app.state.settings so handlers reach them via
request.app.state.settings without a module global.

apps/api/app.py mirrors apps/cli/main.py's sys.path.insert(...) at
module top so apps.api can import core.* when loaded by path.

The module-level app is the uvicorn entry point
(uvicorn apps.api.app:app). It is constructed at import time from real
env settings; tests should prefer create_app(...) with injected settings.

Endpoints added in later D sessions (contract reserved now):

POST /telegram/webhook (D4) — Telegram pushes updates here. Requires the
X-Telegram-Bot-Api-Secret-Token header (D2/D4). Unauthorized updates are
rejected with 200 OK and no side effect (destination §11).

text

**Replace the stale "Not yet defined" section** with:

```markdown
## Not yet defined (will be added here when built)

- `POST /telegram/webhook` handler (D4)
- `parse_update` / `is_authorized` / `send_message` (D2/D3)
- Tool interface (`core.tools.Tool`) — Milestone G
- Agent contract (task/output shape every agent returns) — Milestone H
- Task graph node schema — Milestone I
Edit 4 — docs/MILESTONE_D_PLAN.md
Two mechanical fixes. The decision numbers in the "Likely decisions to log" section collide with existing entries D011–D013, and the "Settings via core/config.py" line contradicts D014.

Replace the "Likely decisions to log" block with:

markdown
## Decisions logged (see DECISIONS.md)
- **D014 — Interface settings live in `apps/api/settings.py`, wrapping `core.config.Settings`; `core/` is not edited.** (Logged at D1.)
- **D015 — Telegram auth = user-id allowlist + webhook secret header.** (To be logged at D2.)
- **D016 — Milestone D is synchronous** (request handler calls the model and replies inline). Background workers for long tasks are Milestone F; note the known limitation (Telegram webhooks time out ~seconds). (To be logged at D4.)
Fix the config line in "New dependencies / config / secrets":

Replace:

Settings additions (via core/config.py, env-sourced): telegram_bot_token, telegram_allowed_user_ids (parse comma-separated → tuple[int,...]), telegram_webhook_secret, public_base_url.

With:

ApiSettings additions (apps/api/settings.py, env-sourced; see D014): telegram_bot_token, telegram_allowed_user_ids (parse comma-separated → tuple[int,...]), telegram_webhook_secret, public_base_url. core/config.py is not edited.

## Telegram parsing + auth (apps/api/telegram.py) — Session 11 (D2)

```python
@dataclass(frozen=True)
class IncomingMessage:
    update_id: int
    user_id: int
    chat_id: int
    text: str

def parse_update(payload: Any) -> IncomingMessage | None: ...
def is_authorized(user_id: int, settings: ApiSettings) -> bool: ...
Agreements:

parse_update consumes a Telegram update dict and returns an
IncomingMessage for a plain text message from a user. It returns None
for every other shape: non-dict payloads, missing/mistyped keys, non-message
updates (edited_message, channel_post, callback_query, …), empty/whitespace
text, non-string text. It never raises on malformed input.

is_authorized(user_id, settings) returns user_id in settings.telegram_allowed_user_ids. An empty allowlist denies everyone.

Both are pure, side-effect-free, and take their settings explicitly — no
globals, no env reads. Tests construct real ApiSettings with fake values.

The webhook-secret header check is not here; it belongs to the HTTP
layer (D4's handler in apps/api/app.py), because it inspects request
headers, not the update body.

text

**`docs/progress.json`** — this is the one I got wrong at D1. To prevent that: add the S11 entry and fix the pointer fields, but **do not commit until you paste the validator output**. The edit is:

Add to `completed_bricks` (after S10):

```json
    {
      "id": "S11",
      "title": "Telegram update parsing + allowlist auth (Milestone D, D2)",
      "files": [
        "apps/api/telegram.py (IncomingMessage, parse_update, is_authorized)",
        "apps/api/settings.py (extended: 4 Telegram fields + masking repr)",
        "tests/test_telegram_auth.py"
      ],
      "tests_passing": "<N>",
      "total_tests_after": "<97+N>",
      "commit": "<fill after commit>",
      "verification_level": 2
    }
Note verification_level: 2 — D2 has no L3. It becomes L3 when the phone test at D5 proves the whole path, at which point I'll bump it retroactively in the S11 entry (or add a note).

Fix the top-level pointers:

json
  "current_brick": "D3 (next) = S12 - thin Telegram send_message client",
  "next_brick": "S12",
Update handoff_note to end with the S11 line. Then run the validator before committing:

bash
python -c "import json; d=json.load(open('docs/progress.json')); print('valid', len(d['completed_bricks']), d['completed_bricks'][-1]['id'], d['next_brick'])"
Expect: valid 13 S11 S12

## Not yet defined (will be added here when built)

- Constitution repository create/read/append (`core.memory.constitution`) — Session 8
- Tool interface (`core.tools.Tool`) — Session ~9+
- Agent contract (task/output shape every agent returns) — Session ~11+
- Task graph node schema — Session ~13+
- Project Constitution schema — Session ~6+ (Stage 3)
