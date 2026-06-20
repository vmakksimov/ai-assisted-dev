"""FastAPI application factory.

Wires logging, the DB engine lifespan, CORS, a request-ID middleware, exception
handlers, and routers. No module-level side effects beyond exposing ``app``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api.routers import health, reviews
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.infrastructure.db.session import dispose_engine, init_engine

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize the DB engine on startup, dispose it on shutdown."""
    init_engine()
    log.info("app_startup")
    try:
        yield
    finally:
        await dispose_engine()
        log.info("app_shutdown")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind a per-request id into structlog context and echo it back."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="DevGuard AI",
        version=settings.app_version,
        description="AI-powered Pull Request Risk Analyzer and Test Suggestion Assistant.",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    register_exception_handlers(app)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(reviews.router, prefix="/api/v1")
    return app


app = create_app()
