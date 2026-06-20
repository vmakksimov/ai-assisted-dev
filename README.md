# DevGuard AI

> AI-powered Pull Request Risk Analyzer and Test Suggestion Assistant.

Paste a Git/PR unified diff (or upload a `.diff`/`.patch`), and DevGuard AI uses Google
Gemini to flag risky changes, write review comments, and suggest unit + integration
tests — saving every analysis to a searchable history.

This repository contains **Module 1**: the core web application. See
[`CLAUDE.md`](./CLAUDE.md) for architecture, scope boundaries, and conventions.

---

## Stack

- **Backend:** FastAPI (async) · SQLAlchemy 2.0 async · asyncpg · Alembic · Pydantic v2
- **Database:** PostgreSQL
- **LLM:** Google Gemini (`google-genai`), default `gemini-2.5-flash`
- **Frontend:** React + TypeScript + Vite + Material UI + React Query
- **Tooling:** pip · ruff · mypy · pytest

## Prerequisites

- Docker + Docker Compose (the only requirement for the one-command setup below)
- A Google Gemini API key
- For local (non-Docker) development: Python 3.12+ and Node.js 20+

## Quickstart — everything in Docker (recommended)

Run the whole stack (PostgreSQL + backend + frontend) with one command.

```bash
cp .env.example .env
# edit .env and set GEMINI_API_KEY

docker compose up -d --build
```

That's it:

- **Frontend:** http://localhost:5173
- **Backend API docs:** http://localhost:8009/docs
- **Health:** http://localhost:8009/api/v1/health

The backend container applies database migrations automatically on startup.
Stop everything with `docker compose down` (add `-v` to also wipe the database volume).

## Local development (without Docker)

Run only PostgreSQL in Docker, and the apps on your host.

### 1. Configure environment

```bash
cp .env.example .env        # set GEMINI_API_KEY
```

### 2. Start PostgreSQL

```bash
docker compose up -d db
```

### 3. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .\.venv\Scripts\activate     macOS/Linux:  source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8009
```

API docs: http://localhost:8009/docs · Health: http://localhost:8009/api/v1/health

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Tests

```bash
# backend (Gemini mocked). Integration tests need a DEDICATED test DB:
cd backend
docker exec devguard-db psql -U devguard -d devguard -c "CREATE DATABASE devguard_test;"   # once
TEST_DATABASE_URL=postgresql+asyncpg://devguard:devguard@localhost:5432/devguard_test python -m pytest

cd frontend && npm run test          # frontend
```

## Project layout

See [`CLAUDE.md`](./CLAUDE.md#repository-layout) for the full annotated tree and the
Clean Architecture layering rules.

## Roadmap (future modules)

Module 1 builds the seams; these arrive later:

- **Module 2:** GitHub/GitLab PR integration, authentication.
- **Module 3:** vector DB + RAG over codebase context.
- **Later:** LangChain/LangGraph multi-agent review workflows, n8n automation.

## License

MIT © 2026 Viktor Maksimov — see [`LICENSE`](./LICENSE).
