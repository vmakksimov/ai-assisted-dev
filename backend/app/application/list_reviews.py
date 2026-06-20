"""Use case: list review history (paginated, filterable)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities import Page
from app.domain.enums import ReviewStatus, RiskSeverity
from app.domain.interfaces import ReviewRepository


@dataclass(frozen=True)
class ListReviewsQuery:
    """Input to the list use case."""

    limit: int = 20
    offset: int = 0
    status: ReviewStatus | None = None
    overall_risk: RiskSeverity | None = None


class ListReviewsUseCase:
    """Returns a paginated page of review summaries."""

    def __init__(self, *, repository: ReviewRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListReviewsQuery) -> Page:
        return await self._repository.list(
            limit=query.limit,
            offset=query.offset,
            status=query.status,
            overall_risk=query.overall_risk,
        )
