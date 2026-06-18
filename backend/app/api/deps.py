"""Dependency injection wiring.

Builds use cases from their ports per request. The ``LLMAnalyzer`` is provided here so
tests can override it via ``app.dependency_overrides[get_analyzer]``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analyze_diff import AnalyzeDiffUseCase
from app.application.get_review import DeleteReviewUseCase, GetReviewUseCase
from app.application.list_reviews import ListReviewsUseCase
from app.core.config import Settings, get_settings
from app.domain.interfaces import LLMAnalyzer
from app.infrastructure.db.repositories import SqlAlchemyReviewRepository
from app.infrastructure.db.session import get_session
from app.infrastructure.diff.unified_diff_parser import UnifiedDiffParser
from app.infrastructure.llm.gemini_client import GeminiAnalyzer

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@lru_cache
def _build_analyzer() -> GeminiAnalyzer:
    settings = get_settings()
    return GeminiAnalyzer(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )


def get_analyzer() -> LLMAnalyzer:
    """Provide the LLM analyzer port. Overridden in tests."""
    return _build_analyzer()


AnalyzerDep = Annotated[LLMAnalyzer, Depends(get_analyzer)]


def get_repository(session: SessionDep) -> SqlAlchemyReviewRepository:
    return SqlAlchemyReviewRepository(session)


RepositoryDep = Annotated[SqlAlchemyReviewRepository, Depends(get_repository)]


def get_analyze_use_case(
    repository: RepositoryDep,
    analyzer: AnalyzerDep,
    settings: SettingsDep,
) -> AnalyzeDiffUseCase:
    return AnalyzeDiffUseCase(
        parser=UnifiedDiffParser(max_diff_bytes=settings.max_diff_bytes),
        analyzer=analyzer,
        repository=repository,
        model_name=settings.gemini_model,
    )


def get_list_use_case(repository: RepositoryDep) -> ListReviewsUseCase:
    return ListReviewsUseCase(repository=repository)


def get_get_use_case(repository: RepositoryDep) -> GetReviewUseCase:
    return GetReviewUseCase(repository=repository)


def get_delete_use_case(repository: RepositoryDep) -> DeleteReviewUseCase:
    return DeleteReviewUseCase(repository=repository)


AnalyzeUseCaseDep = Annotated[AnalyzeDiffUseCase, Depends(get_analyze_use_case)]
ListUseCaseDep = Annotated[ListReviewsUseCase, Depends(get_list_use_case)]
GetUseCaseDep = Annotated[GetReviewUseCase, Depends(get_get_use_case)]
DeleteUseCaseDep = Annotated[DeleteReviewUseCase, Depends(get_delete_use_case)]
