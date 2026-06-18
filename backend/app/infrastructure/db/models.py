"""SQLAlchemy 2.0 ORM models for review history.

Native PostgreSQL enums mirror ``app/domain/enums.py``. The ``reviews`` aggregate owns
three child collections via cascading relationships. These ORM rows never leave the
repository — they are mapped to/from domain entities there.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.enums import (
    CommentSeverity,
    DiffSource,
    Priority,
    ReviewStatus,
    RiskCategory,
    RiskSeverity,
    TestType,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    """Persist/declare native enums by their *value* (e.g. "paste"), not the member
    name ("PASTE"). This matches the lowercase values created in the Alembic migration.
    """
    return [member.value for member in enum_cls]


def _pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(enum_cls, name=name, metadata=Base.metadata, values_callable=_enum_values)


# Native PG enum types defined once and reused across columns/tables so the type is
# created exactly once (avoids duplicate CREATE TYPE on metadata.create_all in tests).
_risk_severity = _pg_enum(RiskSeverity, "risk_severity")
_risk_category = _pg_enum(RiskCategory, "risk_category")
_review_status = _pg_enum(ReviewStatus, "review_status")
_diff_source = _pg_enum(DiffSource, "diff_source")
_comment_severity = _pg_enum(CommentSeverity, "comment_severity")
_test_type = _pg_enum(TestType, "test_type")
_priority = _pg_enum(Priority, "priority")


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


def _review_fk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class ReviewModel(Base):
    """One analysis run (aggregate root)."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = _uuid_pk()
    # Reserved for future auth; never populated in Module 1.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_text: Mapped[str] = mapped_column(Text, nullable=False)
    diff_source: Mapped[DiffSource] = mapped_column(_diff_source, nullable=False)
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_risk: Mapped[RiskSeverity | None] = mapped_column(_risk_severity, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        _review_status, nullable=False, default=ReviewStatus.PENDING
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    risk_findings: Mapped[list[RiskFindingModel]] = relationship(
        back_populates="review", cascade="all, delete-orphan", lazy="selectin"
    )
    review_comments: Mapped[list[ReviewCommentModel]] = relationship(
        back_populates="review", cascade="all, delete-orphan", lazy="selectin"
    )
    test_suggestions: Mapped[list[TestSuggestionModel]] = relationship(
        back_populates="review", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_reviews_created_at", created_at.desc()),
        Index("ix_reviews_status", status),
    )


class RiskFindingModel(Base):
    """A risky change identified in the diff."""

    __tablename__ = "risk_findings"

    id: Mapped[uuid.UUID] = _uuid_pk()
    review_id: Mapped[uuid.UUID] = _review_fk()
    severity: Mapped[RiskSeverity] = mapped_column(_risk_severity, nullable=False)
    category: Mapped[RiskCategory] = mapped_column(_risk_category, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    review: Mapped[ReviewModel] = relationship(back_populates="risk_findings")


class ReviewCommentModel(Base):
    """An inline review remark."""

    __tablename__ = "review_comments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    review_id: Mapped[uuid.UUID] = _review_fk()
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[CommentSeverity] = mapped_column(_comment_severity, nullable=False)

    review: Mapped[ReviewModel] = relationship(back_populates="review_comments")


class TestSuggestionModel(Base):
    """A suggested unit or integration test."""

    __tablename__ = "test_suggestions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    review_id: Mapped[uuid.UUID] = _review_fk()
    test_type: Mapped[TestType] = mapped_column(_test_type, nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    example_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[Priority] = mapped_column(_priority, nullable=False)

    review: Mapped[ReviewModel] = relationship(back_populates="test_suggestions")
