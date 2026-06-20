"""Use cases: fetch and delete a single review."""

from __future__ import annotations

import uuid

from app.core.exceptions import ReviewNotFoundError
from app.domain.entities import Review
from app.domain.interfaces import ReviewRepository


class GetReviewUseCase:
    """Fetches a full review by id, raising if it does not exist."""

    def __init__(self, *, repository: ReviewRepository) -> None:
        self._repository = repository

    async def execute(self, review_id: uuid.UUID) -> Review:
        review = await self._repository.get(review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {review_id} not found.")
        return review


class DeleteReviewUseCase:
    """Deletes a review (cascading its children)."""

    def __init__(self, *, repository: ReviewRepository) -> None:
        self._repository = repository

    async def execute(self, review_id: uuid.UUID) -> None:
        deleted = await self._repository.delete(review_id)
        if not deleted:
            raise ReviewNotFoundError(f"Review {review_id} not found.")
