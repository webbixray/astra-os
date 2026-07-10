"""Add campaign budgets, templates, ab_tests, ab_test_variants

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaign_budgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("total_budget", sa.Float, default=0.0, nullable=False),
        sa.Column("spent", sa.Float, default=0.0, nullable=False),
        sa.Column("currency", sa.String(3), default="USD", nullable=False),
        sa.Column("alert_threshold", sa.Float, default=80.0, nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "campaign_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("channels", ARRAY(sa.String), default=list, nullable=False),
        sa.Column("objective", sa.String(100), nullable=True),
        sa.Column("budget_amount", sa.Float, nullable=True),
        sa.Column("budget_currency", sa.String(3), default="USD", nullable=False),
        sa.Column("default_duration_days", sa.Integer, default=30, nullable=False),
        sa.Column("config", JSONB, default=dict, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ab_tests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("status", sa.String(50), default="draft", nullable=False, index=True),
        sa.Column("goal_metric", sa.String(50), default="conversion_rate", nullable=False),
        sa.Column("winner_variant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ab_test_variants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ab_test_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("config", JSONB, default=dict, nullable=False),
        sa.Column("traffic_percent", sa.Float, default=50.0, nullable=False),
        sa.Column("impressions", sa.Integer, default=0, nullable=False),
        sa.Column("clicks", sa.Integer, default=0, nullable=False),
        sa.Column("conversions", sa.Integer, default=0, nullable=False),
        sa.Column("spend", sa.Float, default=0.0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ab_test_variants")
    op.drop_table("ab_tests")
    op.drop_table("campaign_templates")
    op.drop_table("campaign_budgets")
