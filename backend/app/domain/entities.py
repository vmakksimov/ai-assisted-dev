"""Domain entities — plain dataclasses with no framework dependencies.

Repositories and use cases speak in these types. They are mapped to/from ORM rows in the
repository and to/from DTOs in the API layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import (
    CommentSeverity,
    DiffSource,
    Priority,
    ReviewStatus,
    RiskCategory,
    RiskSeverity,
    TestType,
)


@dataclass
class RiskFinding:
    """A single risky change identified in the diff."""

    severity: RiskSeverity
    category: RiskCategory
    title: str
    description: str
    file_path: str | None = None
    line_hint: str | None = None
    recommendation: str | None = None
    id: uuid.UUID | None = None


@dataclass
class ReviewComment:
    """An inline review remark."""

    comment: str
    severity: CommentSeverity
    file_path: str | None = None
    line_hint: str | None = None
    id: uuid.UUID | None = None


@dataclass
class TestSuggestion:
    """A suggested unit or integration test."""

    test_type: TestType
    target: str
    description: str
    priority: Priority
    example_code: str | None = None
    id: uuid.UUID | None = None


@dataclass
class DiffStats:
    """Parsed statistics about a diff."""

    files_changed: int
    additions: int
    deletions: int


@dataclass
class AnalysisResult:
    """The structured result produced by the LLM analyzer (port output)."""

    overall_risk: RiskSeverity
    summary: str
    risk_findings: list[RiskFinding] = field(default_factory=list)
    review_comments: list[ReviewComment] = field(default_factory=list)
    test_suggestions: list[TestSuggestion] = field(default_factory=list)
    raw_response: dict[str, object] | None = None


@dataclass
class Review:
    """A single analysis run and its persisted results — the aggregate root."""

    diff_text: str
    diff_source: DiffSource
    stats: DiffStats
    model_name: str
    status: ReviewStatus = ReviewStatus.PENDING
    title: str | None = None
    owner_id: uuid.UUID | None = None  # reserved for future auth; unused in Module 1
    overall_risk: RiskSeverity | None = None
    summary: str | None = None
    error_message: str | None = None
    raw_response: dict[str, object] | None = None
    risk_findings: list[RiskFinding] = field(default_factory=list)
    review_comments: list[ReviewComment] = field(default_factory=list)
    test_suggestions: list[TestSuggestion] = field(default_factory=list)
    id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def apply_analysis(self, result: AnalysisResult) -> None:
        """Populate this review from a successful analysis result."""
        self.overall_risk = result.overall_risk
        self.summary = result.summary
        self.risk_findings = result.risk_findings
        self.review_comments = result.review_comments
        self.test_suggestions = result.test_suggestions
        self.raw_response = result.raw_response
        self.status = ReviewStatus.COMPLETED

    def mark_failed(self, message: str) -> None:
        """Record a hard analysis failure without losing the review."""
        self.status = ReviewStatus.FAILED
        self.error_message = message


@dataclass
class ReviewSummary:
    """Lightweight projection of a review for history listings."""

    id: uuid.UUID
    title: str | None
    status: ReviewStatus
    overall_risk: RiskSeverity | None
    diff_source: DiffSource
    files_changed: int
    created_at: datetime


@dataclass
class Page:
    """A paginated slice of review summaries."""

    items: list[ReviewSummary]
    total: int
    limit: int
    offset: int
