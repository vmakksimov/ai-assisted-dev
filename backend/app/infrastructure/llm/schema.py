"""Pydantic schema for Gemini's structured JSON output.

This schema is sent to Gemini as ``response_schema`` and used to validate the response.
Enum fields constrain the model to valid values. The validated payload is mapped to
domain entities by the adapter — these Pydantic models never leave the LLM layer.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    CommentSeverity,
    Priority,
    RiskCategory,
    RiskSeverity,
    TestType,
)


class RiskFindingOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: RiskSeverity
    category: RiskCategory
    title: str
    description: str
    file_path: str | None = None
    line_hint: str | None = None
    recommendation: str | None = None


class ReviewCommentOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: CommentSeverity
    comment: str
    file_path: str | None = None
    line_hint: str | None = None


class TestSuggestionOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_type: TestType
    target: str
    description: str
    priority: Priority
    example_code: str | None = None


class GeminiAnalysis(BaseModel):
    """Top-level structured analysis returned by Gemini."""

    model_config = ConfigDict(extra="ignore")

    overall_risk: RiskSeverity
    summary: str
    risk_findings: list[RiskFindingOut] = Field(default_factory=list)
    review_comments: list[ReviewCommentOut] = Field(default_factory=list)
    test_suggestions: list[TestSuggestionOut] = Field(default_factory=list)
