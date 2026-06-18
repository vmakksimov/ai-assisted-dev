"""Initial review-history schema.

Creates the pgcrypto extension (for gen_random_uuid), the native enum types, and the
reviews aggregate with its risk_findings, review_comments, and test_suggestions children.

Revision ID: 0001
Revises:
Create Date: 2026-06-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Native enum types (created once, referenced by columns with create_type=False).
risk_severity = postgresql.ENUM(
    "low", "medium", "high", "critical", name="risk_severity", create_type=False
)
risk_category = postgresql.ENUM(
    "security",
    "performance",
    "correctness",
    "maintainability",
    "style",
    name="risk_category",
    create_type=False,
)
review_status = postgresql.ENUM(
    "pending", "completed", "failed", "partial", name="review_status", create_type=False
)
diff_source = postgresql.ENUM("paste", "upload", name="diff_source", create_type=False)
comment_severity = postgresql.ENUM(
    "info", "minor", "major", name="comment_severity", create_type=False
)
test_type = postgresql.ENUM("unit", "integration", name="test_type", create_type=False)
priority = postgresql.ENUM("low", "medium", "high", name="priority", create_type=False)

_ALL_ENUMS = (
    risk_severity,
    risk_category,
    review_status,
    diff_source,
    comment_severity,
    test_type,
    priority,
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    for enum in _ALL_ENUMS:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("diff_text", sa.Text(), nullable=False),
        sa.Column("diff_source", diff_source, nullable=False),
        sa.Column("files_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("additions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deletions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_risk", risk_severity, nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", review_status, nullable=False, server_default="pending"),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_created_at", "reviews", [sa.text("created_at DESC")])
    op.create_index("ix_reviews_status", "reviews", ["status"])

    op.create_table(
        "risk_findings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severity", risk_severity, nullable=False),
        sa.Column("category", risk_category, nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line_hint", sa.String(length=64), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_findings_review_id", "risk_findings", ["review_id"])

    op.create_table(
        "review_comments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line_hint", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("severity", comment_severity, nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_comments_review_id", "review_comments", ["review_id"])

    op.create_table(
        "test_suggestions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_type", test_type, nullable=False),
        sa.Column("target", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("example_code", sa.Text(), nullable=True),
        sa.Column("priority", priority, nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_suggestions_review_id", "test_suggestions", ["review_id"])


def downgrade() -> None:
    op.drop_table("test_suggestions")
    op.drop_table("review_comments")
    op.drop_table("risk_findings")
    op.drop_index("ix_reviews_status", table_name="reviews")
    op.drop_index("ix_reviews_created_at", table_name="reviews")
    op.drop_table("reviews")

    bind = op.get_bind()
    for enum in reversed(_ALL_ENUMS):
        enum.drop(bind, checkfirst=True)
