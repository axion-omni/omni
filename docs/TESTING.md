# Testing

## Strategy

| Test type | Covers | Status in this repo |
|---|---|---|
| Unit | One function/class, dependencies mocked | 4 tests, `tests/test_anthropic_provider.py` |
| Integration | Real components talking to each other | None yet — needed from Session 6+ (state + memory) |
| Failure | Deliberately broken input/dependency | 2 of the 4 current tests are failure-path tests |
| Security | Injection, permission bypass | Needed from the Tool System onward (Session ~9+) |
| AI behavior | Output meets quality criteria, not just "ran" | Needed from Session ~11+ (agent evaluation) |
| Regression | A fixed bug stays fixed | Add per-bug starting whenever the first bug is found |

## Current test suite

```
pytest -v
```
Expected: `4 passed`, no network or API key required (client is mocked via
`client_factory` injection — see `tests/test_anthropic_provider.py`).

## Live verification (separate from automated tests, on purpose)

```
python scripts/smoke_test.py
```
Requires a real `ANTHROPIC_API_KEY` in `.env`. Hits the real network and
costs a small amount of real money. Not run by CI or by default — this is
the "Level 3" check per the build protocol: proof the system works on your
actual machine with your actual credentials, not just proof the mocked
contract holds.

## Verification levels (per project protocol)

1. **Generated** — code exists, unverified. Worth nothing on its own.
2. **Tested in the AI's environment** — the assistant ran `pytest` and it
   passed there.
3. **Verified on your machine** — you ran `pytest -v` and `smoke_test.py`
   yourself. **This is the only level that counts as "done."**

No brick is marked complete in PROJECT_STATE.md until it has reached level 3.
