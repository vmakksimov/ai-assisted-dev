---
name: async-programming
description: Async/await discipline for DevGuard AI — never block the event loop, async DB sessions, timeouts and retries for Gemini, concurrency with gather, cancellation, and the sync-to-threadpool escape hatch. Load when writing async code.
---

# Async programming (DevGuard AI)

## Core rule: never block the event loop
- All I/O is `async`: DB (SQLAlchemy async + asyncpg), HTTP, Gemini calls.
- Use plain `def` only for pure, non-awaiting helpers. Anything doing I/O is `async def`.
- Never call blocking functions (`time.sleep`, sync `requests`, blocking file I/O, CPU-heavy
  loops) inside an `async def`. They freeze the whole server.
- If a dependency is sync-only, wrap it: `await asyncio.to_thread(fn, *args)` (or
  `run_in_executor`). If the `google-genai` SDK call is invoked synchronously, offload it
  this way — or use its async API if available.

## Async DB sessions
- Use `async_sessionmaker(engine, expire_on_commit=False)`.
- One `AsyncSession` per request, provided by the `get_session` dependency.
- `await session.execute(...)`, `await session.commit()`, `await session.refresh(obj)`.
- Don't share a session across tasks; sessions are not concurrency-safe.

## Timeouts & retries (Gemini)
- Always bound external calls with a timeout (`settings.gemini_timeout_seconds`):
  `async with asyncio.timeout(t): ...` (3.11+).
- Retry only **transient** errors (timeouts, 5xx, rate limits) with bounded attempts and
  exponential backoff + jitter. Never retry validation or auth errors.
- Cap total retries (`settings.gemini_max_retries`); on exhaustion, raise a domain
  `LLMError` so the use case can persist `status="failed"`.

## Concurrency
- Use `asyncio.gather(...)` for independent awaitables (e.g. parallel sub-analyses later).
  In Module 1 the analysis is a single call — don't over-engineer.
- Prefer `asyncio.TaskGroup` (3.11+) when spawning structured concurrent tasks; it
  cancels siblings on failure.

## Cancellation
- Respect cancellation: let `CancelledError` propagate (don't swallow it). Clean up in
  `finally` blocks.
- Keep critical sections (DB commit) short so a client disconnect doesn't corrupt state.

## Testing async code
- Use `pytest-asyncio` (`asyncio_mode = "auto"`). See the `pytest-testing` skill.
- Fake the `LLMAnalyzer` port with an async stub; never hit the network in tests.
