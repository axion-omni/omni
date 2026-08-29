# START HERE — run it & verify on your own PC

**What this is:** the AI Project Execution Engine (heading toward a phone-based
personal AI OS). **Milestone 1** (talk to models: abstraction, registry, routing,
retry) is code-complete; **Milestone C** (persistent state on Postgres) is in
progress. Everything so far is **Level 2** — tested in the build sandbox but
**never run by a human**. Your job on this PC is the real run (**Level 3**).

Full map for continuing the build: **`docs/BUILD_INSTRUCTIONS_INDEX.md`**.

---

## 1. Setup (about 5 minutes)
Needs **Python 3.12+** (3.14 also works). In this folder:

**Windows (PowerShell):**
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
**macOS / Linux:**
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Run the tests (no keys, no database needed)
```
pytest -v
```
Expect **59 passed, 2 skipped**. The 2 skips are live-database tests (they run in
step 4). This is the Level-2 baseline — confirm it before anything else.

## 3. Level-3 check A — talk to a model (verifies Sessions 2–5)
Put a key in `.env`. **Cheapest path (free, no card): OpenRouter** —
```
ACTIVE_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...your key...
```
(or use Anthropic: set `ANTHROPIC_API_KEY=...` and leave `ACTIVE_PROVIDER=anthropic`.)
Then run the same prompt under two policies (edit `MODEL_POLICY` in `.env`):
```
python apps/cli/main.py "say hello"                 # MODEL_POLICY=cheap
python apps/cli/main.py "say hello"                 # MODEL_POLICY=quality
```
You should get a real reply, and the stderr line
`[provider/model — N in / M out — policy=… -> …]` should change between
**cheap** (`cheap-fast`) and **quality** (`reasoning-strong`). That verifies the
model pipeline end-to-end. Cost: a couple of tiny calls (free on OpenRouter).

## 4. Level-3 check B — the database (verifies Sessions 6–7)
**Option 1 — Docker (easiest):**
```
docker compose -f infra/docker-compose.yml up -d
```
then in `.env`: `DATABASE_URL=postgresql://engine:engine@localhost:5432/engine`

**Option 2 — Supabase:** create a free project, enable the `vector` extension,
and copy the **direct (port 5432)** connection string into `.env` as
`DATABASE_URL` (not the 6543 pooled one).

Then:
```
python infra/migrate.py     # creates the projects + constitutions tables
pytest -v                    # now 61 passed, 0 skipped (the 2 live tests run)
python infra/migrate.py     # run again -> "already up to date"
```

## 5. Tell me the results
Report back what you saw for steps 2–4 (pass counts, the two policy lines, and
whether migrate + the live DB tests passed). Once you confirm, I mark Sessions
2–7 as **Level 3** in `docs/PROJECT_STATE.md` — the only level that counts as
done — and we continue with **Session 8** (`docs/MILESTONE_C_PLAN.md`).

---

## Notes
- `.env` holds secrets and is git-ignored — never commit or share it.
- Each brick is a real git commit; **keep the `.git` folder** in the zip (it's the record).
- If `pytest` isn't found, use `python -m pytest -v`.
- The reference docs at the repo root (`*_SPECIFICATION*.md`, `AI_Project_Execution_Engine.md`, etc.) are background reading, intentionally not part of the app.
