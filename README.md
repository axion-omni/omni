# AI Project Execution Engine — Build Repo

This is the live implementation of the destination architecture defined in
`docs/00_MASTER_ARCHITECTURE.md`. Built brick by brick, ~3 hours/day.

## Status
See `docs/12_PROGRESS.md` for exactly where the build is right now.

## Quickstart
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
pytest -v
python scripts/smoke_test.py   # requires a real API key, hits the network
```
