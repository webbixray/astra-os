"""Add campaigns and content tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-09
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), default="draft", nullable=False, index=True),
        sa.Column("budget_amount", sa.Float, nullable=True),
        sa.Column("budget_currency", sa.String(3), default="USD", nullable=False),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("channels", ARRAY(sa.String), default=list, nullable=False),
        sa.Column("objective", sa.String(100), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("ai_generated", sa.Boolean, default=False, nullable=False),
        sa.Column("metadata", JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_campaigns_org_status", "campaigns", ["organization_id", "status"])

    op.create_table(
        "content",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("body", sa.Text, default="", nullable=False),
        sa.Column("status", sa.String(50), default="draft", nullable=False, index=True),
        sa.Column("brand_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("generated_by_ai", sa.Boolean, default=False, nullable=False),
        sa.Column("version", sa.Integer, default=1, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_content_org_status", "content", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_table("content")
    op.drop_table("campaigns")
