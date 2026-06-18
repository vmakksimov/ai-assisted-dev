"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep, SettingsDep
from app.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: SessionDep, settings: SettingsDep) -> HealthResponse:
    """Liveness probe that also verifies database connectivity."""
    db_status = "up"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"
    return HealthResponse(status="ok", db=db_status, version=settings.app_version)
