"""Add multi-tenant org features: parent_org_id, invitations, feature flags, usage, billing

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("parent_org_id", UUID(as_uuid=True), nullable=True, index=True),
    )
    op.create_table(
        "org_invitations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("invited_by_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), default="member", nullable=False),
        sa.Column("status", sa.String(50), default="pending", nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "org_feature_flags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column("config", JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "org_usage_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("value", sa.Float, default=0.0, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "org_billing_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("plan_tier", sa.String(50), default="free", nullable=False),
        sa.Column("billing_cycle", sa.String(50), default="monthly", nullable=False),
        sa.Column("subscription_status", sa.String(50), default="active", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("org_billing_plans")
    op.drop_table("org_usage_records")
    op.drop_table("org_feature_flags")
    op.drop_table("org_invitations")
    op.drop_column("organizations", "parent_org_id")
