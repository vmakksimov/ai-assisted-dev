"""Application configuration via pydantic-settings.

All configuration flows through the cached ``Settings`` object. Never read
``os.environ`` elsewhere in the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# config.py -> core -> app -> backend -> repo root.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent

# Load the repo-root .env first, then backend/.env (the latter overrides), so a single
# .env at the repo root is picked up no matter which directory the process runs from.
_ENV_FILES = (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """Typed application settings loaded from environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database ---------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://devguard:devguard@localhost:5432/devguard",
        description="Async SQLAlchemy DSN (postgresql+asyncpg://...).",
    )

    # --- Gemini -----------------------------------------------------------
    gemini_api_key: str = Field(default="", description="Google Gemini API key.")
    gemini_model: str = Field(default="gemini-2.5-flash", description="Gemini model name.")
    gemini_timeout_seconds: float = Field(default=60.0, gt=0)
    gemini_max_retries: int = Field(default=2, ge=0)

    # --- Application ------------------------------------------------------
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="console", description="'console' or 'json'.")
    max_diff_bytes: int = Field(default=200_000, gt=0)
    # NoDecode: don't JSON-decode the env value; the validator below splits it manually.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    app_version: str = Field(default="0.1.0")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow CORS origins as a comma-separated env string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def _normalize_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton ``Settings`` instance."""
    return Settings()
