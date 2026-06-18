"""Port interfaces (Protocols) the application layer depends on.

Concrete adapters in ``app/infrastructure`` implement these. Use cases never import the
adapters directly — they receive a Protocol-typed collaborator via constructor injection.
This is the seam that lets future modules swap implementations (e.g. a multi-agent
LangGraph analyzer) without touching the application or domain layers.
"""

from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from app.domain.entities import (
    AnalysisResult,
    DiffStats,
    Page,
    Review,
)
from app.domain.enums import ReviewStatus, RiskSeverity


@runtime_checkable
class DiffParser(Protocol):
    """Parses and validates a unified diff, returning normalized text + stats."""

    def parse(self, raw_diff: str) -> tuple[str, DiffStats]:
        """Validate and normalize ``raw_diff``.

        Returns the normalized (possibly truncated) diff text and its statistics.
        Raises ``ValidationError`` for non-diff input and ``DiffTooLargeError`` when
        oversized beyond what truncation allows.
        """
        ...


@runtime_checkable
class LLMAnalyzer(Protocol):
    """Analyzes a diff with an LLM and returns a structured result."""

    async def analyze(self, diff_text: str) -> AnalysisResult:
        """Run analysis on ``diff_text``.

        Raises ``LLMError`` (or ``LLMTimeoutError``) on failure or unparseable output.
        """
        ...


@runtime_checkable
class ReviewRepository(Protocol):
    """Persistence port for reviews. Speaks in domain entities, never ORM rows."""

    async def add(self, review: Review) -> Review:
        """Persist a new review (with its children) and return it with ids populated."""
        ...

    async def get(self, review_id: uuid.UUID) -> Review | None:
        """Return the full review (with children) or ``None`` if absent."""
        ...

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: ReviewStatus | None = None,
        overall_risk: RiskSeverity | None = None,
    ) -> Page:
        """Return a paginated, optionally filtered page of review summaries."""
        ...

    async def delete(self, review_id: uuid.UUID) -> bool:
        """Delete a review (cascading children). Returns ``True`` if a row was removed."""
        ...
