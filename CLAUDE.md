# DevGuard AI

DevGuard AI is an **AI-powered Pull Request Risk Analyzer and Test Suggestion Assistant**.

It accepts Git/PR unified diffs, analyzes them with Google Gemini to identify risky
changes, generates review comments, and suggests unit + integration tests. Every
analysis is persisted to PostgreSQL and surfaced through a FastAPI backend and a
React + TypeScript frontend.

---

## Module 1 scope

Module 1 is intentionally narrow. It delivers a working end-to-end web application:

1. Accept a unified diff via **paste** or **`.diff`/`.patch` file upload**.
2. Analyze it with **Gemini** (configurable model, default `gemini-2.5-flash`).
3. Produce **risk findings**, **review comments**, and **test suggestions**.
4. Persist each analysis as **review history** in **PostgreSQL**.
5. Expose a **FastAPI** API consumed by a **React** frontend.

### Out of scope for Module 1 (future work)

These are deliberately **not** implemented now. Architectural seams exist so they can
be added without rewrites, but writing any of them in Module 1 is scope creep:

- **Authentication / users** — no login, registration, JWT, sessions, password
  hashing, or RBAC. History is global. A nullable `owner_id` column exists on tables
  as a forward-compat seam only. → Module 2/3.
- **GitHub / GitLab integration** — no fetching diffs from PR URLs or Git host APIs.
- **Vector DB / RAG / embeddings.**
- **LangChain / LangGraph / multi-agent workflows.**
- **n8n automation.**

When in doubt, consult the **Scope Guardian** agent (`.claude/agents/scope-guardian.md`).

---

## Architecture — Clean Architecture

Dependencies point **inward**. Inner layers know nothing about outer layers.

| Layer | Location | Knows about | Never imports |
|---|---|---|---|
| **Domain** | `app/domain/` | Nothing external | FastAPI, SQLAlchemy, Gemini, Pydantic models |
| **Application** | `app/application/` | Domain only | Frameworks, adapters |
| **Infrastructure** | `app/infrastructure/` | Domain interfaces | API layer |
| **API / Presentation** | `app/api/` | Application + domain | — |
| **Core (cross-cutting)** | `app/core/` | config, logging, exceptions | business logic |

**The dependency rule:** `domain` imports nothing from the rest of the app. Use cases
in `application` depend only on **Protocols** defined in `app/domain/interfaces.py`.
Concrete adapters (Gemini, SQLAlchemy, diff parser) live in `infrastructure` and
implement those Protocols. They are wired together in `app/api/deps.py`.

**Why:** swapping Gemini for a future multi-agent LangGraph pipeline = a new adapter
implementing `LLMAnalyzer`, with use cases untouched. Adding RAG = a new Protocol +
adapter injected into the use case. No inner-layer changes.

---

## Tech stack

| Concern | Choice |
|---|---|
| Python deps / env | **pip** + `requirements.txt` / `requirements-dev.txt` (+ venv) |
| Containerization | **Docker Compose** (db + backend + frontend) |
| Web framework | **FastAPI** (async) |
| ORM | **SQLAlchemy 2.0** (async) + **asyncpg** |
| Migrations | **Alembic** (async env) |
| Validation / settings | **Pydantic v2** + **pydantic-settings** |
| LLM | **Google Gemini** via `google-genai` |
| Logging | **structlog** (JSON) |
| Tests | **pytest** + **pytest-asyncio** + **httpx** |
| Lint / format | **ruff** |
| Types | **mypy** |
| Frontend | **React + TypeScript + Vite** |
| UI | **Material UI (MUI)** |
| Data fetching | **React Query** + **axios** |
| Routing | **React Router** |

---

## Dev workflow

**Whole stack in Docker** (from repo root) — the simplest path:

```bash
cp .env.example .env                      # set GEMINI_API_KEY
docker compose up -d --build              # db + backend (:8009) + frontend (:5173)
```

The backend container runs `alembic upgrade head` on startup. Frontend at
http://localhost:5173, API docs at http://localhost:8009/docs.

**Backend on the host** (run from `backend/`, deps via pip + venv):

```bash
python -m venv .venv                      # then activate it
python -m pip install -r requirements-dev.txt
docker compose up -d db                   # start Postgres (from repo root)
python -m alembic upgrade head            # apply migrations
python -m uvicorn app.main:app --reload --port 8009   # serve at http://localhost:8009
# Tests need a dedicated test DB (the suite drops tables in teardown):
TEST_DATABASE_URL=postgresql+asyncpg://devguard:devguard@localhost:5432/devguard_test python -m pytest
python -m ruff check . && python -m ruff format --check .
python -m mypy app
```

**Frontend** (run from `frontend/`):

```bash
npm install
npm run dev                               # Vite dev server
npm run test                              # Vitest
npm run build
```

---

## Coding conventions

- **Async everywhere** for I/O (DB, HTTP, Gemini). Never block the event loop; push
  unavoidable sync work to a threadpool.
- **Type hints are mandatory.** mypy must pass. Public functions are fully annotated.
- **Pydantic at boundaries, dataclasses in the domain.** API DTOs and the Gemini
  response schema are Pydantic models. Domain entities are plain `@dataclass` objects
  with no framework imports.
- **No business logic in routers.** Routers parse the request, call a use case, and
  serialize the result. Orchestration lives in `application/`.
- **Repositories return domain entities,** not ORM rows. Mapping happens inside the
  repository.
- **Structured logging** with a request/correlation ID. Never log secrets or full
  diff bodies at `INFO`.
- **Errors** use the domain exception hierarchy and are translated to a consistent
  JSON envelope by centralized handlers.

## Error handling contract

Domain raises typed exceptions (`app/core/exceptions.py`). Centralized FastAPI handlers
(`app/core/exception_handlers.py`) map them to a stable envelope:

```json
{ "error": { "type": "ValidationError", "message": "...", "detail": null } }
```

Gemini failures degrade gracefully: the review row is still persisted with
`status = "failed"` (or `"partial"`) and an `error_message`, so the record is never lost.

## Configuration

All config flows through `pydantic-settings` (`app/core/config.py`). Required env vars:

| Var | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | async Postgres DSN (`postgresql+asyncpg://...`) | — |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `GEMINI_MODEL` | model name | `gemini-2.5-flash` |
| `LOG_LEVEL` | logging level | `INFO` |
| `MAX_DIFF_BYTES` | diff truncation limit | `200000` |
| `CORS_ORIGINS` | comma-separated allowed origins | `http://localhost:5173` |

See `.env.example`.

## Testing

Pyramid; **no real Gemini calls in CI** (the `LLMAnalyzer` port is faked). Unit tests
cover the diff parser, prompt builder, use cases, and schema validation. Integration
tests run the API against a real test Postgres with a stubbed Gemini adapter. See
`.claude/skills/pytest-testing` and the plan in §9.

## Scope discipline

Any change that implements a future-module feature (auth, Git host integration, RAG,
LangChain/LangGraph, n8n, multi-agent) must be flagged and justified before merging.
Keep Module 1 focused. The **Scope Guardian** agent exists to enforce this.

## Subagents (`.claude/agents/`)

- **architect** — layer boundaries, interfaces, where code belongs.
- **backend** — FastAPI, use cases, repositories, models, migrations.
- **frontend** — React pages/components/hooks, API types, MUI.
- **ai-integration** — Gemini adapter, prompts, structured output, retries.
- **testing** — test pyramid, fixtures, fake LLM port, coverage.
- **scope-guardian** — rejects scope creep into future modules.

## Agent context (`.claudeignore`)

This is the **single** project guide — there are no per-folder `CLAUDE.md` files.
`.claudeignore` at the repo root lists paths agents/tools should skip (secrets, virtual
envs, `node_modules`, build output, caches, lockfiles, DB volumes) to keep context
focused on source. Update it when adding new generated or vendored directories.
