"""Unit tests for AnalyzeDiffUseCase using a fake repo and fake analyzer."""

from __future__ import annotations

import uuid

import pytest
from app.application.analyze_diff import AnalyzeDiffCommand, AnalyzeDiffUseCase
from app.core.exceptions import LLMError, ValidationError
from app.domain.entities import Page, Review
from app.domain.enums import DiffSource, ReviewStatus
from app.infrastructure.diff.unified_diff_parser import UnifiedDiffParser

from tests.fixtures.fake_analyzer import FakeAnalyzer, failing_analyzer
from tests.fixtures.sample_diffs import NOT_A_DIFF, VALID_DIFF


class FakeRepository:
    """In-memory ReviewRepository for unit tests."""

    def __init__(self) -> None:
        self.saved: list[Review] = []

    async def add(self, review: Review) -> Review:
        review.id = uuid.uuid4()
        self.saved.append(review)
        return review

    async def get(self, review_id: uuid.UUID) -> Review | None:
        return next((r for r in self.saved if r.id == review_id), None)

    async def list(self, **_: object) -> Page:
        return Page(items=[], total=0, limit=20, offset=0)

    async def delete(self, review_id: uuid.UUID) -> bool:
        before = len(self.saved)
        self.saved = [r for r in self.saved if r.id != review_id]
        return len(self.saved) < before


def _use_case(analyzer: FakeAnalyzer, repo: FakeRepository) -> AnalyzeDiffUseCase:
    return AnalyzeDiffUseCase(
        parser=UnifiedDiffParser(max_diff_bytes=200_000),
        analyzer=analyzer,
        repository=repo,
        model_name="gemini-2.5-flash",
    )


async def test_successful_analysis_is_persisted_completed() -> None:
    repo = FakeRepository()
    use_case = _use_case(FakeAnalyzer(), repo)

    review = await use_case.execute(
        AnalyzeDiffCommand(raw_diff=VALID_DIFF, diff_source=DiffSource.PASTE, title="t")
    )

    assert review.status is ReviewStatus.COMPLETED
    assert review.overall_risk is not None
    assert len(review.risk_findings) == 1
    assert len(review.test_suggestions) == 2
    assert repo.saved[0].id == review.id


async def test_invalid_diff_raises_before_calling_llm() -> None:
    repo = FakeRepository()
    analyzer = FakeAnalyzer()
    use_case = _use_case(analyzer, repo)

    with pytest.raises(ValidationError):
        await use_case.execute(
            AnalyzeDiffCommand(raw_diff=NOT_A_DIFF, diff_source=DiffSource.PASTE)
        )

    assert analyzer.calls == []  # LLM never called
    assert repo.saved == []  # nothing persisted


async def test_llm_failure_persists_failed_review_and_reraises() -> None:
    repo = FakeRepository()
    use_case = _use_case(failing_analyzer(), repo)

    with pytest.raises(LLMError):
        await use_case.execute(
            AnalyzeDiffCommand(raw_diff=VALID_DIFF, diff_source=DiffSource.PASTE)
        )

    # The review is not lost — it is saved with a failed status.
    assert len(repo.saved) == 1
    assert repo.saved[0].status is ReviewStatus.FAILED
    assert repo.saved[0].error_message
