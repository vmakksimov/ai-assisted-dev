"""Shared pytest fixtures.

Unit tests need none of the DB machinery. Integration tests use a real Postgres pointed
at by ``TEST_DATABASE_URL`` (falling back to ``DATABASE_URL``); if neither is reachable,
those tests are skipped so the unit suite still runs anywhere.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.api.deps import get_analyzer
from app.infrastructure.db.models import Base
from app.infrastructure.db.session import get_session
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.fixtures.fake_analyzer import FakeAnalyzer

# IMPORTANT: require a *dedicated* TEST_DATABASE_URL. We intentionally do NOT fall back
# to DATABASE_URL — the fixture drops every table in teardown, which would wipe a real
# dev database. If TEST_DATABASE_URL is unset, integration tests skip. If it accidentally
# points at the dev DATABASE_URL, we refuse to run.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
_DEV_DATABASE_URL = os.getenv("DATABASE_URL")


@pytest_asyncio.fixture
async def db_engine():  # type: ignore[no-untyped-def]
    """Create a schema in a dedicated test database; drop it afterwards.

    Skips the test if no dedicated test database is configured/reachable.
    """
    if not TEST_DATABASE_URL:
        pytest.skip(
            "Set TEST_DATABASE_URL (a dedicated test DB) to run integration tests. "
            "It must differ from DATABASE_URL — the suite drops all tables in teardown."
        )
    if _DEV_DATABASE_URL and TEST_DATABASE_URL == _DEV_DATABASE_URL:
        pytest.fail(
            "TEST_DATABASE_URL must not equal DATABASE_URL — integration tests drop all "
            "tables and would destroy your dev data. Use a separate database."
        )

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # connection refused, auth, etc.
        await engine.dispose()
        pytest.skip(f"Test database not reachable: {exc}")

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    """An AsyncClient with DB session and a fake analyzer wired in."""
    app = create_app()
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _session_override() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_analyzer] = lambda: FakeAnalyzer()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
