"""Add brand_voices and content_templates tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_voices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tone", sa.String(50), server_default="professional", nullable=False),
        sa.Column("vocabulary", ARRAY(sa.String), server_default="{}", nullable=False),
        sa.Column("style_guide", sa.Text, server_default="", nullable=False),
        sa.Column("target_audience", sa.Text, server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "content_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(50), server_default="blog", nullable=False),
        sa.Column("description", sa.Text, server_default="", nullable=False),
        sa.Column("sections", JSONB, server_default="[]", nullable=False),
        sa.Column("variables", ARRAY(sa.String), server_default="{}", nullable=False),
        sa.Column("system_prompt", sa.Text, server_default="", nullable=False),
        sa.Column("is_builtin", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content_templates")
    op.drop_table("brand_voices")
