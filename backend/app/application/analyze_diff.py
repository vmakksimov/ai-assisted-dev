"""Use case: analyze a diff and persist the resulting review."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.domain.entities import Review
from app.domain.enums import DiffSource
from app.domain.interfaces import DiffParser, LLMAnalyzer, ReviewRepository

log = get_logger(__name__)


@dataclass(frozen=True)
class AnalyzeDiffCommand:
    """Input to the analyze use case."""

    raw_diff: str
    diff_source: DiffSource
    title: str | None = None


class AnalyzeDiffUseCase:
    """Parses a diff, runs LLM analysis, and persists the review.

    A Gemini failure does not lose the review: the row is still saved with
    ``status="failed"`` and an error message, then re-raised so the API can respond
    appropriately.
    """

    def __init__(
        self,
        *,
        parser: DiffParser,
        analyzer: LLMAnalyzer,
        repository: ReviewRepository,
        model_name: str,
    ) -> None:
        self._parser = parser
        self._analyzer = analyzer
        self._repository = repository
        self._model_name = model_name

    async def execute(self, command: AnalyzeDiffCommand) -> Review:
        # Parse + validate up front; raises ValidationError/DiffTooLargeError on bad input.
        diff_text, stats = self._parser.parse(command.raw_diff)

        review = Review(
            diff_text=diff_text,
            diff_source=command.diff_source,
            stats=stats,
            model_name=self._model_name,
            title=command.title,
        )
        log.info(
            "analysis_started",
            diff_source=command.diff_source,
            diff_bytes=len(diff_text.encode("utf-8")),
            files_changed=stats.files_changed,
            model=self._model_name,
        )

        try:
            result = await self._analyzer.analyze(diff_text)
            review.apply_analysis(result)
        except LLMError as exc:
            review.mark_failed(exc.message)
            saved = await self._repository.add(review)
            log.warning("analysis_failed", review_id=str(saved.id), error=exc.message)
            raise

        saved = await self._repository.add(review)
        log.info(
            "analysis_completed",
            review_id=str(saved.id),
            overall_risk=saved.overall_risk,
            risk_findings=len(saved.risk_findings),
            test_suggestions=len(saved.test_suggestions),
            review_comments=len(saved.review_comments),
        )
        return saved
