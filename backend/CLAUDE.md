# Backend — DevGuard AI

Async FastAPI backend. See the root [`CLAUDE.md`](../CLAUDE.md) for architecture, scope,
and conventions. This file is the backend-specific quick reference.

## Layout (Clean Architecture, dependencies point inward)

- `app/domain/` — entities (dataclasses), enums, port Protocols. **No framework imports.**
- `app/application/` — use cases (classes). Depend on `domain` only.
- `app/infrastructure/` — adapters: `db/` (session, models, repository), `llm/` (Gemini,
  prompts, schema), `diff/` (parser). Implement the domain ports.
- `app/api/` — routers (thin), DTO `schemas.py`, DI `deps.py`.
- `app/core/` — config, logging, exceptions, exception handlers.
- `migrations/` — Alembic (async env).

## Commands

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# Integration tests need a DEDICATED test DB (they drop all tables in teardown).
# Set TEST_DATABASE_URL to a separate database, never your dev DATABASE_URL:
TEST_DATABASE_URL=postgresql+asyncpg://devguard:devguard@localhost:5432/devguard_test uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy app
```

> Native enums persist by **value** (lowercase, e.g. `paste`) via `values_callable` in
> `infrastructure/db/models.py`, matching the Alembic migration. Don't remove that — the
> DB enum types use lowercase values, not the `StrEnum` member names.

## Rules of thumb

- Async for all I/O. Plain functions for routes/helpers; classes for use cases,
  repositories, adapters (constructor injection).
- Gemini is reached only through the `LLMAnalyzer` port — never import `google-genai`
  outside `infrastructure/llm/`.
- Repositories map ORM ⇄ domain entities; ORM rows never escape `infrastructure/db/`.
- Raise domain exceptions (`app/core/exceptions.py`); handlers produce the error envelope.
- Tests fake the `LLMAnalyzer`; never call real Gemini in CI.

## New native enum?

Add it to `app/domain/enums.py`, define a reusable `SAEnum(..., metadata=Base.metadata)`
instance in `infrastructure/db/models.py`, and create/drop it explicitly in a migration.
