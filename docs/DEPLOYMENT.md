# Deployment Runbook — Milestone D (Cloud API + Telegram)

This is the operator runbook for putting the Cloud API on Render and
registering the Telegram webhook. It is the Level-3 execution path for
Milestone D — the milestone closes only when a message sent from a real
phone reaches the deployed engine and a reply returns.

Executed top to bottom, this runbook takes the working local system from
D1–D4 and makes it reachable from Telegram. If anything fails, stop at the
failing step; every later step depends on the earlier ones being green.

## Prerequisites

You already have (from earlier sessions):

- A Telegram bot created via @BotFather → `TELEGRAM_BOT_TOKEN`
- Your numeric Telegram user id (from @userinfobot) → `TELEGRAM_ALLOWED_USER_IDS`
- A random webhook secret → `TELEGRAM_WEBHOOK_SECRET`
  (generated with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- A Supabase Postgres from Milestone C → `DATABASE_URL`
- A model provider key → `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY`
- All of the above set in your local `.env` and the local suite green at 130 tests

You need to create:

- A Render account (free tier is sufficient)
- A Render Web Service pointed at `github.com/axion-omni/omni`

## Step 1 — Create the Render Web Service

1. Sign in to https://dashboard.render.com
2. **New +** → **Web Service**
3. Connect the GitHub repo `axion-omni/omni` (grant Render access on first use)
4. Fill the form:
   - **Name:** `omni-api` (must be unique across Render; if taken, pick another)
   - **Region:** whichever is nearest you
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn apps.api.app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
   - **Health Check Path:** `/health`
   - **Auto-Deploy:** Yes
5. **Do not click Create yet.** Open the **Environment** section first (Step 2).

## Step 2 — Set the environment variables

In the same **New Web Service** form, under **Environment Variables**, add
each of these. Values come from your local `.env` — copy them by hand. Do
not commit any of these to the repo.

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | your bot token from BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | your numeric Telegram id (comma-separated if more than one) |
| `TELEGRAM_WEBHOOK_SECRET` | the same random string you generated locally |
| `PUBLIC_BASE_URL` | **leave blank for now** — filled after first deploy |
| `ACTIVE_PROVIDER` | `anthropic` or `openrouter` |
| `ANTHROPIC_API_KEY` | your Anthropic key (or leave blank if using OpenRouter) |
| `OPENROUTER_API_KEY` | your OpenRouter key (or leave blank) |
| `OPENROUTER_MODEL` | the model slug your local `.env` uses |
| `MODEL_POLICY` | `balanced` (or whatever your local `.env` uses) |
| `MODEL_FALLBACK` | optional; leave blank unless your local `.env` sets it |
| `DATABASE_URL` | the Supabase connection string from your local `.env` |

Now click **Create Web Service**. Render starts a first build and deploy.
Watch the log pane — the build should finish in a couple of minutes.

## Step 3 — Verify the deploy

When Render says **Live**, copy the public URL from the top of the service
page — it looks like `https://omni-api-xxxx.onrender.com`.

Test the health endpoint:

```bash
curl -s https://omni-api-xxxx.onrender.com/health
# expect: {"status":"ok"}
