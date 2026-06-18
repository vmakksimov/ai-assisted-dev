"""API request/response DTOs (Pydantic v2).

These are presentation-shaped and mapped explicitly from domain entities. The error
envelope shape is documented here for the OpenAPI spec and frontend type generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities import Review, ReviewSummary
from app.domain.enums import (
    CommentSeverity,
    DiffSource,
    Priority,
    ReviewStatus,
    RiskCategory,
    RiskSeverity,
    TestType,
)


# --- Requests -------------------------------------------------------------
class AnalyzeDiffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diff_text: str = Field(min_length=1, description="Raw unified diff text.")
    title: str | None = Field(default=None, max_length=200)


# --- Nested response parts ------------------------------------------------
class RiskFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None
    severity: RiskSeverity
    category: RiskCategory
    title: str
    description: str
    file_path: str | None
    line_hint: str | None
    recommendation: str | None


class ReviewCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None
    severity: CommentSeverity
    comment: str
    file_path: str | None
    line_hint: str | None


class TestSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None
    test_type: TestType
    target: str
    description: str
    priority: Priority
    example_code: str | None


class DiffStatsResponse(BaseModel):
    files_changed: int
    additions: int
    deletions: int


# --- Top-level responses --------------------------------------------------
class ReviewResponse(BaseModel):
    """Full review with nested findings, comments, and tests."""

    id: uuid.UUID
    title: str | None
    status: ReviewStatus
    diff_source: DiffSource
    overall_risk: RiskSeverity | None
    summary: str | None
    error_message: str | None
    model_name: str
    stats: DiffStatsResponse
    diff_text: str
    risk_findings: list[RiskFindingResponse]
    review_comments: list[ReviewCommentResponse]
    test_suggestions: list[TestSuggestionResponse]
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, review: Review) -> ReviewResponse:
        assert review.id is not None
        return cls(
            id=review.id,
            title=review.title,
            status=review.status,
            diff_source=review.diff_source,
            overall_risk=review.overall_risk,
            summary=review.summary,
            error_message=review.error_message,
            model_name=review.model_name,
            stats=DiffStatsResponse(
                files_changed=review.stats.files_changed,
                additions=review.stats.additions,
                deletions=review.stats.deletions,
            ),
            diff_text=review.diff_text,
            risk_findings=[RiskFindingResponse.model_validate(f) for f in review.risk_findings],
            review_comments=[
                ReviewCommentResponse.model_validate(c) for c in review.review_comments
            ],
            test_suggestions=[
                TestSuggestionResponse.model_validate(t) for t in review.test_suggestions
            ],
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


class ReviewSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    status: ReviewStatus
    overall_risk: RiskSeverity | None
    diff_source: DiffSource
    files_changed: int
    created_at: datetime

    @classmethod
    def from_entity(cls, summary: ReviewSummary) -> ReviewSummaryResponse:
        return cls.model_validate(summary)


class PaginatedReviews(BaseModel):
    items: list[ReviewSummaryResponse]
    total: int
    limit: int
    offset: int


# --- Error envelope (documentation) --------------------------------------
class ErrorDetail(BaseModel):
    type: str
    message: str
    detail: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    db: str
    version: str
