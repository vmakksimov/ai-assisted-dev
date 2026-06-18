"""Closed value sets shared across layers.

These ``StrEnum`` members are the single source of truth for the corresponding
PostgreSQL native enums and the Gemini structured-output schema. Keep them in sync.
"""

from __future__ import annotations

from enum import StrEnum


class RiskSeverity(StrEnum):
    """Severity of a risk finding and the overall review verdict."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(StrEnum):
    """Lifecycle status of a review run."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DiffSource(StrEnum):
    """How the diff was supplied."""

    PASTE = "paste"
    UPLOAD = "upload"


class RiskCategory(StrEnum):
    """Category taxonomy for a risk finding."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"


class CommentSeverity(StrEnum):
    """Severity of an inline review comment."""

    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"


class TestType(StrEnum):
    """Kind of suggested test."""

    UNIT = "unit"
    INTEGRATION = "integration"


class Priority(StrEnum):
    """Priority of a suggested test."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
