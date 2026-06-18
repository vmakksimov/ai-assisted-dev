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
- **Tooling:** uv · ruff · mypy · pytest

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (for local PostgreSQL)
- A Google Gemini API key

## Quickstart

### 1. Configure environment

```bash
cp .env.example .env
# edit .env and set GEMINI_API_KEY
```

### 2. Start PostgreSQL

```bash
docker compose up -d db
```

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs · Health: http://localhost:8000/api/v1/health

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Tests

```bash
cd backend && uv run pytest          # backend (Gemini mocked)
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
