"""FastAPI exception handlers mapping domain errors to the standard error envelope.

Envelope shape (stable contract the frontend relies on):

    { "error": { "type": "ValidationError", "message": "...", "detail": null } }
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DevGuardError,
    DiffTooLargeError,
    LLMError,
    ReviewNotFoundError,
    UnsupportedUploadError,
    ValidationError,
)
from app.core.logging import get_logger

log = get_logger(__name__)

# Domain exception -> HTTP status.
_STATUS_MAP: dict[type[DevGuardError], int] = {
    ValidationError: 422,  # Unprocessable Content
    DiffTooLargeError: 413,  # Content Too Large
    UnsupportedUploadError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ReviewNotFoundError: status.HTTP_404_NOT_FOUND,
    LLMError: status.HTTP_502_BAD_GATEWAY,
}


def _envelope(exc_type: str, message: str, detail: object | None = None) -> dict[str, object]:
    return {"error": {"type": exc_type, "message": message, "detail": detail}}


def _status_for(exc: DevGuardError) -> int:
    for exc_cls, code in _STATUS_MAP.items():
        if isinstance(exc, exc_cls):
            return code
    return status.HTTP_400_BAD_REQUEST


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the app."""

    @app.exception_handler(DevGuardError)
    async def _handle_domain(_: Request, exc: DevGuardError) -> JSONResponse:
        code = _status_for(exc)
        if code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            log.error("domain_error", type=type(exc).__name__, message=exc.message)
        return JSONResponse(
            status_code=code,
            content=_envelope(type(exc).__name__, exc.message, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,  # Unprocessable Content
            content=_envelope("ValidationError", "Request validation failed.", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_error", type=type(exc).__name__, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("InternalServerError", "An unexpected error occurred."),
        )
