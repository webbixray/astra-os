"""Add advertising tables (ad_accounts, ad_campaigns, ad_creatives, ad_insights)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ad_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("platform_account_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), server_default="disconnected"),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("timezone", sa.String(50), server_default="America/New_York"),
        sa.Column("credentials", sa.JSON(), server_default="{}"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ad_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ad_account_id", UUID(as_uuid=True), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("objective", sa.String(50), server_default="awareness"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("platform_campaign_id", sa.String(255), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("daily_budget", sa.Float(), server_default="0"),
        sa.Column("lifetime_budget", sa.Float(), server_default="0"),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("start_date", sa.String(20), nullable=True),
        sa.Column("end_date", sa.String(20), nullable=True),
        sa.Column("targeting", sa.JSON(), server_default="{}"),
        sa.Column("creatives", sa.JSON(), server_default="[]"),
        sa.Column("sync_status", sa.String(50), server_default="not_synced"),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ad_creatives",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ad_campaign_id", UUID(as_uuid=True), sa.ForeignKey("ad_campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), server_default="image"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("headline", sa.Text(), server_default=""),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("destination_url", sa.String(1024), server_default=""),
        sa.Column("asset_urls", sa.JSON(), server_default="[]"),
        sa.Column("platform_creative_ids", sa.JSON(), server_default="{}"),
        sa.Column("dimensions", sa.JSON(), server_default="{}"),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ad_insights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ad_account_id", UUID(as_uuid=True), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ad_campaign_id", UUID(as_uuid=True), sa.ForeignKey("ad_campaigns.id", ondelete="CASCADE"), nullable=True),
        sa.Column("date", sa.String(20), nullable=False, index=True),
        sa.Column("impressions", sa.Integer(), server_default="0"),
        sa.Column("clicks", sa.Integer(), server_default="0"),
        sa.Column("spend", sa.Float(), server_default="0"),
        sa.Column("conversions", sa.Integer(), server_default="0"),
        sa.Column("revenue", sa.Float(), server_default="0"),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("ad_campaign_id", "date", name="uq_insight_per_campaign_date"),
    )


def downgrade() -> None:
    op.drop_table("ad_insights")
    op.drop_table("ad_creatives")
    op.drop_table("ad_campaigns")
    op.drop_table("ad_accounts")
