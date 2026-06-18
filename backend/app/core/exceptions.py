"""Domain exception hierarchy.

The application and domain layers raise these typed exceptions; they never raise
``HTTPException``. The API layer maps them to HTTP responses and the standard error
envelope (see ``app/core/exception_handlers.py``).
"""

from __future__ import annotations


class DevGuardError(Exception):
    """Base class for all DevGuard domain errors."""

    def __init__(self, message: str, *, detail: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class ValidationError(DevGuardError):
    """Input failed validation (empty diff, not a unified diff, etc.). -> 422"""


class DiffTooLargeError(DevGuardError):
    """The diff exceeds ``MAX_DIFF_BYTES``. -> 413"""


class UnsupportedUploadError(DevGuardError):
    """Uploaded file is not a supported ``.diff``/``.patch`` type. -> 415"""


class ReviewNotFoundError(DevGuardError):
    """No review exists for the requested id. -> 404"""


class LLMError(DevGuardError):
    """Gemini failed or returned output that could not be validated. -> 502"""


class LLMTimeoutError(LLMError):
    """A transient, retryable timeout talking to Gemini."""
