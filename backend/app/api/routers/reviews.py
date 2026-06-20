"""Review analysis and history endpoints.

Routers are thin: parse the request, call a use case, serialize the result. No business
logic, DB access, or Gemini calls here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Form, Query, UploadFile, status

from app.api.deps import (
    AnalyzeUseCaseDep,
    DeleteUseCaseDep,
    GetUseCaseDep,
    ListUseCaseDep,
    SettingsDep,
)
from app.api.schemas import (
    AnalyzeDiffRequest,
    PaginatedReviews,
    ReviewResponse,
    ReviewSummaryResponse,
)
from app.application.analyze_diff import AnalyzeDiffCommand
from app.application.list_reviews import ListReviewsQuery
from app.core.exceptions import DiffTooLargeError, UnsupportedUploadError
from app.domain.enums import DiffSource, ReviewStatus, RiskSeverity

router = APIRouter(prefix="/reviews", tags=["reviews"])

_ALLOWED_UPLOAD_SUFFIXES = (".diff", ".patch", ".txt")


@router.post(
    "/analyze",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_diff(
    request: AnalyzeDiffRequest,
    use_case: AnalyzeUseCaseDep,
) -> ReviewResponse:
    """Analyze a pasted unified diff and persist the review."""
    review = await use_case.execute(
        AnalyzeDiffCommand(
            raw_diff=request.diff_text,
            diff_source=DiffSource.PASTE,
            title=request.title,
        )
    )
    return ReviewResponse.from_entity(review)


@router.post(
    "/analyze/upload",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_uploaded_diff(
    use_case: AnalyzeUseCaseDep,
    settings: SettingsDep,
    file: UploadFile,
    title: str | None = Form(default=None),
) -> ReviewResponse:
    """Analyze an uploaded ``.diff``/``.patch`` file."""
    filename = file.filename or ""
    if not filename.lower().endswith(_ALLOWED_UPLOAD_SUFFIXES):
        raise UnsupportedUploadError(
            "Unsupported file type. Upload a .diff, .patch, or .txt file."
        )

    raw = await file.read()
    if len(raw) > settings.max_diff_bytes * 5:
        raise DiffTooLargeError("Uploaded diff is too large to analyze.")

    review = await use_case.execute(
        AnalyzeDiffCommand(
            raw_diff=raw.decode("utf-8", errors="replace"),
            diff_source=DiffSource.UPLOAD,
            title=title,
        )
    )
    return ReviewResponse.from_entity(review)


@router.get("", response_model=PaginatedReviews)
async def list_reviews(
    use_case: ListUseCaseDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: ReviewStatus | None = Query(default=None, alias="status"),
    overall_risk: RiskSeverity | None = Query(default=None),
) -> PaginatedReviews:
    """Return a paginated, optionally filtered page of review history."""
    page = await use_case.execute(
        ListReviewsQuery(
            limit=limit,
            offset=offset,
            status=status_filter,
            overall_risk=overall_risk,
        )
    )
    return PaginatedReviews(
        items=[ReviewSummaryResponse.from_entity(item) for item in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: uuid.UUID, use_case: GetUseCaseDep) -> ReviewResponse:
    """Return a single full review by id."""
    review = await use_case.execute(review_id)
    return ReviewResponse.from_entity(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: uuid.UUID, use_case: DeleteUseCaseDep) -> None:
    """Delete a review and its children."""
    await use_case.execute(review_id)
