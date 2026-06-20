"""SQLAlchemy implementation of the ``ReviewRepository`` port.

All methods accept and return **domain entities**. ORM models never escape this module.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import (
    DiffStats,
    Page,
    Review,
    ReviewComment,
    ReviewSummary,
    RiskFinding,
    TestSuggestion,
)
from app.domain.enums import ReviewStatus, RiskSeverity
from app.infrastructure.db.models import (
    ReviewCommentModel,
    ReviewModel,
    RiskFindingModel,
    TestSuggestionModel,
)


class SqlAlchemyReviewRepository:
    """Persists and retrieves reviews via an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, review: Review) -> Review:
        model = self._to_model(review)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get(self, review_id: uuid.UUID) -> Review | None:
        model = await self._session.get(ReviewModel, review_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: ReviewStatus | None = None,
        overall_risk: RiskSeverity | None = None,
    ) -> Page:
        filters = []
        if status is not None:
            filters.append(ReviewModel.status == status)
        if overall_risk is not None:
            filters.append(ReviewModel.overall_risk == overall_risk)

        total_stmt = select(func.count()).select_from(ReviewModel).where(*filters)
        total = await self._session.scalar(total_stmt) or 0

        rows_stmt = (
            select(ReviewModel)
            .where(*filters)
            .order_by(ReviewModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(rows_stmt)
        items = [self._to_summary(row) for row in result.scalars().all()]
        return Page(items=items, total=total, limit=limit, offset=offset)

    async def delete(self, review_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(ReviewModel).where(ReviewModel.id == review_id)
        )
        return (result.rowcount or 0) > 0

    # --- mapping helpers --------------------------------------------------

    @staticmethod
    def _to_model(review: Review) -> ReviewModel:
        return ReviewModel(
            owner_id=review.owner_id,
            title=review.title,
            diff_text=review.diff_text,
            diff_source=review.diff_source,
            files_changed=review.stats.files_changed,
            additions=review.stats.additions,
            deletions=review.stats.deletions,
            overall_risk=review.overall_risk,
            summary=review.summary,
            status=review.status,
            model_name=review.model_name,
            error_message=review.error_message,
            raw_response=review.raw_response,
            risk_findings=[
                RiskFindingModel(
                    severity=f.severity,
                    category=f.category,
                    file_path=f.file_path,
                    line_hint=f.line_hint,
                    title=f.title,
                    description=f.description,
                    recommendation=f.recommendation,
                )
                for f in review.risk_findings
            ],
            review_comments=[
                ReviewCommentModel(
                    file_path=c.file_path,
                    line_hint=c.line_hint,
                    comment=c.comment,
                    severity=c.severity,
                )
                for c in review.review_comments
            ],
            test_suggestions=[
                TestSuggestionModel(
                    test_type=t.test_type,
                    target=t.target,
                    description=t.description,
                    example_code=t.example_code,
                    priority=t.priority,
                )
                for t in review.test_suggestions
            ],
        )

    @staticmethod
    def _to_entity(model: ReviewModel) -> Review:
        return Review(
            id=model.id,
            owner_id=model.owner_id,
            title=model.title,
            diff_text=model.diff_text,
            diff_source=model.diff_source,
            stats=DiffStats(
                files_changed=model.files_changed,
                additions=model.additions,
                deletions=model.deletions,
            ),
            model_name=model.model_name,
            status=model.status,
            overall_risk=model.overall_risk,
            summary=model.summary,
            error_message=model.error_message,
            raw_response=model.raw_response,
            created_at=model.created_at,
            updated_at=model.updated_at,
            risk_findings=[
                RiskFinding(
                    id=f.id,
                    severity=f.severity,
                    category=f.category,
                    file_path=f.file_path,
                    line_hint=f.line_hint,
                    title=f.title,
                    description=f.description,
                    recommendation=f.recommendation,
                )
                for f in model.risk_findings
            ],
            review_comments=[
                ReviewComment(
                    id=c.id,
                    file_path=c.file_path,
                    line_hint=c.line_hint,
                    comment=c.comment,
                    severity=c.severity,
                )
                for c in model.review_comments
            ],
            test_suggestions=[
                TestSuggestion(
                    id=t.id,
                    test_type=t.test_type,
                    target=t.target,
                    description=t.description,
                    example_code=t.example_code,
                    priority=t.priority,
                )
                for t in model.test_suggestions
            ],
        )

    @staticmethod
    def _to_summary(model: ReviewModel) -> ReviewSummary:
        return ReviewSummary(
            id=model.id,
            title=model.title,
            status=model.status,
            overall_risk=model.overall_risk,
            diff_source=model.diff_source,
            files_changed=model.files_changed,
            created_at=model.created_at,
        )
