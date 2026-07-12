"""Add composite indexes for ad_creatives table.

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-12

Note: The ad_creatives table was already created in migration 0005.
This migration adds additional composite indexes for query performance.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Composite index for org + status queries (creative listing)
    op.create_index(
        "ix_ad_creatives_org_status",
        "ad_creatives",
        ["organization_id", "status"],
    )
    # Index for campaign association queries
    op.create_index(
        "ix_ad_creatives_campaign",
        "ad_creatives",
        ["ad_campaign_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ad_creatives_campaign", table_name="ad_creatives")
    op.drop_index("ix_ad_creatives_org_status", table_name="ad_creatives")
