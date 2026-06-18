---
name: postgresql-sqlalchemy
description: PostgreSQL + SQLAlchemy 2.0 async patterns for DevGuard AI — async engine/session, declarative models, relationships, JSONB, indexing, transactions, and Alembic migration hygiene. Load when working on db models, repositories, or migrations.
---

# PostgreSQL + SQLAlchemy 2.0 async (DevGuard AI)

## Engine & session
- One async engine created at app startup from `settings.database_url`
  (`postgresql+asyncpg://...`), disposed on shutdown via lifespan.
- `async_sessionmaker(engine, expire_on_commit=False)`. Yield an `AsyncSession` per
  request from `get_session`; commit on success, roll back on exception.
- Use `await session.execute(select(...))` and `.scalars()` / `.scalar_one_or_none()`.
  The legacy `Query` API is not used.

## Declarative models (`infrastructure/db/models.py`)
- `class Base(DeclarativeBase): ...`; models use `Mapped[...]` + `mapped_column(...)`.
- UUID PKs: `mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))`
  (requires the `pgcrypto` extension, enabled in the first migration) — or generate in Python.
- Timestamps: `created_at` / `updated_at` as `TIMESTAMPTZ` with
  `server_default=func.now()` and `onupdate=func.now()`.
- Native PG enums via `sqlalchemy.Enum(PyEnum, name="...")`. Keep enum members in sync with
  `app/domain/enums.py`.

## Relationships & cascades
- `reviews` is the parent; `risk_findings`, `test_suggestions`, `review_comments` are children.
- Children declare `review_id` FK with `ondelete="CASCADE"`; parent `relationship(...)` uses
  `cascade="all, delete-orphan"` so deleting a review removes its children.
- Use `selectinload(...)` (not lazy loading) when fetching a review with its collections —
  lazy loads don't work cleanly with async sessions.

## JSONB
- `raw_response` is `mapped_column(JSONB, nullable=True)` for the full validated AI payload
  (audit/debug). Don't query into it for app logic in Module 1 — normalized child rows are
  the queryable source of truth.

## Indexing
- Index foreign keys (`risk_findings.review_id`, etc.) and common filters
  (`reviews.created_at DESC`, `reviews.status`). Declare via `index=True` or `Index(...)`.

## Transactions
- Keep transactions short. The repository writes within the request's session; the session
  boundary (in `get_session`) owns commit/rollback.
- Don't commit inside repository methods unless a method explicitly owns its own unit of
  work — prefer flushing (`await session.flush()`) to get generated IDs, and commit at the edge.

## Repositories
- `SqlAlchemyReviewRepository` implements the `ReviewRepository` Protocol from the domain.
- Methods accept/return **domain entities**, never ORM instances. Map ORM ⇄ entity inside
  the repository so the application layer never sees SQLAlchemy.

## Alembic migration hygiene
- Async Alembic `env.py` (uses the async engine). Run with `uv run alembic ...`.
- Autogenerate is a starting point, not gospel: **review every generated migration**.
  Autogenerate misses enum changes, server defaults, and some index/constraint details —
  fix by hand.
- Enable required extensions (`pgcrypto`) in the first migration before using
  `gen_random_uuid()`.
- One logical change per migration; never edit a migration that's already been applied
  elsewhere — add a new one.
