"""Add content_publishes table

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_publishes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="scheduled", nullable=False, index=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_url", sa.String(1024), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content_publishes")
