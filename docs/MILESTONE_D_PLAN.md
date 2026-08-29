# Milestone D — Cloud API + Telegram bot (Deterministic Build Spec)

> **How to use this file.** Execute the sessions top to bottom. Each is one
> brick: implement → run its Level-2 test gate (green, no network) → operator
> Level-3 → update the six standing docs + `progress.json` → commit. Session
> labels (D1, D2…) map to the next free global `S<n>` when built. If reality
> diverges from this spec, the **code + CONTRACTS.md win** — update this file
> and log a decision. Grounded in: destination architecture §3 (interfaces),
> §5 (Telegram first), §11 (security), §13 (Cloud API), §14 (deploy);
> Construction Spec Part IX (interfaces) & Part XX (security).

> **After this milestone you have an interface on your phone.** A text message
> from Telegram reaches the engine and a reply comes back. It is minimal (one
> synchronous task type, no memory of the conversation, no background work — that
> is Milestones E/F), but it is the first time the PC is not required to use it.

## Definition of done (authoritative gate)
Destination §15 Milestone D: **“A message sent from a phone reaches the
Orchestrator and a reply returns to the phone.”** Verified from a real phone
against the deployed instance (Level 3).

## Prerequisites
- **Milestone C at Level 3** (persistent state; the API will read/write it).
- Milestone B at Level 3 (the API answers by calling the model pipeline).
- **Operator prep (do before D5):**
  - A **Telegram bot**: talk to `@BotFather` → `TELEGRAM_BOT_TOKEN`.
  - Your **numeric Telegram user id** (`@userinfobot`) → `TELEGRAM_ALLOWED_USER_IDS`.
  - A random **webhook secret** string → `TELEGRAM_WEBHOOK_SECRET`.
  - A **Render** (or Fly) web service with a public HTTPS URL; secrets set in its
    manager (never in the repo). Managed Postgres URL from C reused as `DATABASE_URL`.

## New dependencies / config / secrets
- Dependencies: `fastapi`, `uvicorn[standard]` (server), reuse `requests` for
  outbound Telegram calls (no Telegram SDK — same ethos as OpenRouter-over-SDK).
- `Settings` additions (via `core/config.py`, env-sourced): `telegram_bot_token`,
  `telegram_allowed_user_ids` (parse comma-separated → `tuple[int,...]`),
  `telegram_webhook_secret`, `public_base_url`.
- Secrets live in Render’s manager in prod, `.env` locally.

## Contracts introduced (add to CONTRACTS.md as built)
- Cloud API surface: `GET /health`, `POST /telegram/webhook`.
- `apps/api/telegram.py`: `parse_update(payload) -> IncomingMessage|None`,
  `is_authorized(user_id, settings) -> bool`, `send_message(chat_id, text, settings)`.

## Likely decisions to log (DECISIONS.md)
- **D011 — Cloud API = FastAPI; interfaces stay thin (D003).** No business logic
  in `apps/api/` beyond wiring to `core/`.
- **D012 — Telegram auth = user-id allowlist + webhook secret header** as the
  minimum bar (destination §11). Reject everything else silently (200 OK, ignore).
- **D013 — Milestone D is synchronous** (request handler calls the model and
  replies inline). Background workers for long tasks are Milestone F; note the
  known limitation (Telegram webhooks time out ~seconds).

## Sessions

### Session D1 — FastAPI Cloud API skeleton
- **Goal:** a running app with a health check; app factory pattern.
- **Files:** `apps/api/__init__.py`, `apps/api/app.py` (`create_app(settings) ->
  FastAPI`; module-level `app = create_app(load_settings())` for uvicorn),
  `tests/test_api_health.py`. Add fastapi/uvicorn to `requirements.txt`.
- **Steps:** `/health` returns `{"status":"ok"}`. No Telegram yet.
- **Test gate (L2):** `fastapi.testclient.TestClient(app).get("/health")` → 200.
- **Operator L3:** `uvicorn apps.api.app:app` locally → `curl /health` works.
- **Commit:** `feat: Session <n> - FastAPI cloud API skeleton (Milestone D)`.

### Session D2 — Telegram update parsing + auth
- **Goal:** parse a Telegram webhook update and enforce access.
- **Files:** `apps/api/telegram.py` (`parse_update`, `is_authorized`), config
  additions, `tests/test_telegram_auth.py`.
- **Steps:** extract `(user_id, chat_id, text)` from an update; `is_authorized`
  checks the allowlist; the webhook must also require the
  `X-Telegram-Bot-Api-Secret-Token` header to equal `TELEGRAM_WEBHOOK_SECRET`.
- **Test gate (L2):** valid update parses; a non-allowlisted user id is rejected;
  a missing/wrong secret header is rejected. All with fixture payloads, no network.
- **Operator L3:** none yet (covered at D5).
- **Commit:** `feat: Session <n> - Telegram update parsing + allowlist auth`.

### Session D3 — Outbound Telegram client (thin)
- **Goal:** send a message back to a chat.
- **Files:** `send_message(chat_id, text, settings, *, http=requests)` in
  `apps/api/telegram.py`; `tests/test_telegram_send.py`.
- **Steps:** POST to `https://api.telegram.org/bot<token>/sendMessage`; `http`
  injectable so tests assert the payload without a network call.
- **Test gate (L2):** `send_message` builds the correct URL + JSON body (injected
  fake http records the call); non-2xx raises a clear error.
- **Commit:** `feat: Session <n> - thin Telegram send_message client`.

### Session D4 — Wire the webhook to the model pipeline
- **Goal:** message in → model answer out (the end-to-end path, still synchronous).
- **Files:** `POST /telegram/webhook` handler in `apps/api/app.py`;
  `tests/test_api_webhook.py`.
- **Steps:** on an authorized text message, resolve via routing→registry and call
  `generate_with_retry` (reuse Milestone B), then `send_message` the reply.
  Inject the registry/generate + telegram client so the test is offline.
- **Test gate (L2):** a fake authorized update produces a `send_message` call
  whose text is the (faked) model reply; unauthorized update → no send, 200.
- **Operator L3:** none yet (D5).
- **Commit:** `feat: Session <n> - Telegram webhook answers via the model pipeline`.

### Session D5 — Deploy to Render + phone end-to-end (the milestone gate)
- **Goal:** the definition of done, live.
- **Files:** `infra/render.yaml` (web service: `uvicorn apps.api.app:app
  --host 0.0.0.0 --port $PORT`; bind managed Postgres; env from secret manager),
  optional `Dockerfile`; `docs/DEPLOYMENT.md`.
- **Steps (operator):** deploy; run `python infra/migrate.py` against the cloud
  DB (one-off job/shell); register the webhook with Telegram
  (`setWebhook` to `<public_base_url>/telegram/webhook` with the secret token).
- **Test gate (L2):** render config validated; no new unit tests required.
- **Operator L3 — THE GATE:** from your phone, message the bot → a model reply
  returns. Milestone D done.
- **Commit:** `feat: Session <n> - Render deploy + Telegram webhook (Milestone D done)`.

## Security / deploy-safety notes
- Auth is **allowlist + secret header** (destination §11). Never echo secrets;
  treat every field of the update as untrusted input.
- Webhook must be HTTPS with the secret token; reject others with 200-and-ignore
  (don’t leak which users exist).
- Keep the handler fast — Telegram retries on timeout; long work waits for F.

## Explicitly deferred
- Background/async execution and “works while phone closed” → **Milestone F**.
- Conversation memory / grounded answers → **Milestone E**.
- Approval buttons → **Milestone J**. Voice/native app → post-MVP.
