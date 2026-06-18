---
name: pytest-testing
description: Testing strategy for DevGuard AI — pytest + pytest-asyncio, the test pyramid, async DB/client fixtures, faking the LLM port (never hit real Gemini in CI), parametrization, golden fixtures, and coverage. Load when writing or running tests.
---

# Testing (DevGuard AI)

## Stack & config
- `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"` in `pyproject.toml`), `httpx`
  `AsyncClient` for API tests, `pytest-cov` for coverage.
- Tests live in `backend/tests/{unit,integration,fixtures}` with a shared `conftest.py`.
- **Never call the real Gemini API in tests/CI.** The `LLMAnalyzer` Protocol is faked.

## The pyramid
- **Unit (most):** diff parser (valid/invalid/edge diffs), prompt builder (template +
  truncation), use cases with a fake LLM port + fake/in-memory repo, Pydantic schema
  validation incl. malformed AI output → repair/failure path, exception → HTTP mapping.
- **Integration:** FastAPI endpoints via `AsyncClient` against a real **test Postgres**
  with a **stubbed** Gemini adapter — assert persistence, status transitions, cascade
  deletes, pagination, error envelopes.
- **Contract/golden:** canned Gemini JSON fixtures → assert deterministic mapping to
  entities/DTOs. Guards against schema drift.

## Faking the LLM port
- Provide a `FakeAnalyzer` implementing `LLMAnalyzer` that returns a canned
  `GeminiAnalysis` (or raises `LLMError`/`LLMTimeoutError`) based on the input — so success,
  partial, failure, and retry paths are all testable deterministically.
- Inject it via dependency override (`app.dependency_overrides[get_analyzer] = ...`).

## Async fixtures (`conftest.py`)
- `engine` / `session` fixtures using the async engine against a disposable schema or a
  testcontainer Postgres. Create schema per session, truncate/rollback per test for
  isolation (nested transaction + rollback, or recreate).
- `client` fixture wrapping the app in `AsyncClient(transport=ASGITransport(app=app))`
  with DB + analyzer overrides applied.
- Sample diffs and canned Gemini responses live in `tests/fixtures/` and are loaded by
  helper fixtures.

## Style
- Arrange–Act–Assert, one behavior per test. Descriptive names: `test_oversized_diff_returns_413`.
- `@pytest.mark.parametrize` for input matrices (diff variants, severity levels, status flows).
- Assert on behavior and the public contract (status code, envelope, persisted rows), not
  on private internals.

## Coverage & gates
- Enforce a coverage floor on `app/domain` and `app/application` (the logic core).
- CI order: `ruff check` → `mypy app` → unit → integration. Keep unit tests fast (no DB);
  reserve the DB for integration.
