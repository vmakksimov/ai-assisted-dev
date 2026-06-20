---
name: fastapi
description: FastAPI patterns for DevGuard AI — app factory, lifespan, routers, dependency injection, request/response models, status codes, CORS, and keeping logic out of routers. Load when working on the API layer.
---

# FastAPI (DevGuard AI)

## Style: functional at the edges, OOP in the core
- **Routes, dependencies, and small utilities are plain functions** — declarative and
  thin. Follow **RORO** (Receive an Object, Return an Object): take a request DTO, return
  a response DTO.
- **Use cases, repositories, and adapters are classes** with constructor-injected
  collaborators (see `python-best-practices`). Functional edges, object-oriented core.
- Use `async def` for handlers/deps that do I/O; use plain `def` for pure helpers that
  don't await anything — not everything needs to be async.

## App factory + lifespan
- Build the app in a `create_app()` factory in `app/main.py`. Keep module-level side
  effects out of import time.
- Use the `lifespan` async context manager (not `@app.on_event`) to create/dispose the
  async engine, configure logging, and run startup checks.
- Mount routers under a versioned prefix: `app.include_router(reviews.router, prefix="/api/v1")`.

## Routers
- One `APIRouter` per resource in `app/api/routers/` (`health.py`, `reviews.py`).
- Routers are **thin**: validate the request DTO, call a use case via a dependency,
  serialize the result to a response DTO. **No business logic, no DB queries, no Gemini
  calls in routers.**
- Set explicit `status_code` and `response_model` on each route.
- **Guard clauses first, happy path last.** Handle edge cases and error conditions at the
  top of the function with early returns; avoid `else` after a `return`. Keep the main
  success flow at the bottom, unindented.

## Dependency injection
- Wire concrete adapters into use cases in `app/api/deps.py` using `Depends`.
- Provide an async DB session per request via a `get_session` dependency that yields an
  `AsyncSession` and commits/rolls back at the boundary.
- Construct use-case objects from their ports in deps, e.g.:
  ```python
  def get_analyze_use_case(
      session: AsyncSession = Depends(get_session),
      analyzer: LLMAnalyzer = Depends(get_analyzer),
  ) -> AnalyzeDiffUseCase:
      repo = SqlAlchemyReviewRepository(session)
      return AnalyzeDiffUseCase(repo=repo, analyzer=analyzer, parser=UnifiedDiffParser())
  ```
- Keep `Annotated[T, Depends(...)]` aliases for readability where repeated.

## Request / response models
- Use Pydantic v2 DTOs in `app/api/schemas.py`. Separate request and response models.
- Response models mirror the domain but are presentation-shaped (nested findings, tests,
  comments). Map domain entities → DTOs explicitly; don't return ORM rows.
- File uploads use `UploadFile` + `Form` for `multipart/form-data` (the upload endpoint).

## Status codes & errors
- `201` for created reviews, `200` for reads, `204` for delete, `404` for missing,
  `422` for validation, `413` for oversized diffs, `415` for bad upload type,
  `502` for a hard Gemini failure.
- Register centralized exception handlers (see `error-handling` skill) so every error
  returns the `{ "error": { type, message, detail } }` envelope. Don't scatter
  `raise HTTPException` with ad-hoc bodies through the code.

## CORS & config
- Add `CORSMiddleware` configured from `settings.cors_origins`.
- Read all config from the `Settings` object (pydantic-settings); never `os.getenv`
  directly in routers.

## Middleware
- Use middleware for cross-cutting concerns: a request-ID / correlation-ID middleware
  (see the `logging` skill) and timing, applied app-wide rather than per-route.
- Keep middleware lean; heavy logic belongs in use cases.

## Async discipline
- All route handlers and dependencies that do I/O are `async def`.
- Never call blocking code in a handler; see the `async-programming` skill.

## Out of scope for Module 1
- **Caching (Redis / in-memory):** not used in Module 1. Analysis is a single synchronous
  Gemini call per request; there is no caching layer. Revisit if/when latency or cost
  demands it in a later module — do not add it preemptively.
