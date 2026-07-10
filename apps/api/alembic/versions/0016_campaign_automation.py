"""Add campaign automation tables

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budget_allocation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("allocations", JSONB, default=dict, nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "bid_optimization_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("ad_account_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("target_value", sa.Float, default=0.0, nullable=False),
        sa.Column("min_bid", sa.Float, default=0.0, nullable=False),
        sa.Column("max_bid", sa.Float, default=0.0, nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audience_segments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("criteria", JSONB, default=dict, nullable=False),
        sa.Column("predicted_size", sa.Integer, default=0, nullable=False),
        sa.Column("confidence_score", sa.Float, default=0.0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "content_recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("confidence_score", sa.Float, default=0.0, nullable=False),
        sa.Column("metadata", JSONB, default=dict, nullable=False),
        sa.Column("applied", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "automation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_config", JSONB, default=dict, nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_config", JSONB, default=dict, nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("automation_rules")
    op.drop_table("content_recommendations")
    op.drop_table("audience_segments")
    op.drop_table("bid_optimization_rules")
    op.drop_table("budget_allocation_rules")
