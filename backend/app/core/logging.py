"""Structured logging configuration (structlog).

Configured once at startup. Console renderer in dev, JSON in production. Standard-library
logging is routed through structlog so uvicorn / SQLAlchemy logs share the format.
"""

from __future__ import annotations

import logging

import structlog

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog and the stdlib logging bridge."""
    level = getattr(logging, settings.log_level, logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy) through the same level.
    logging.basicConfig(level=level, format="%(message)s")
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
