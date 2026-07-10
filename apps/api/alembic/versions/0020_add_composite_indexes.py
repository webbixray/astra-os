"""Add composite database indexes for common query patterns

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_org_invitations_org_email",
        "org_invitations",
        ["organization_id", "email"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_notifications_user_org_channel_read_archived",
        "notifications",
        ["user_id", "organization_id", "channel", "archived", "is_read"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_org_feature_flags_org_key",
        "org_feature_flags",
        ["organization_id", "feature_key"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_org_usage_records_org_metric_recorded",
        "org_usage_records",
        ["organization_id", "metric", "recorded_at"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("idx_org_invitations_org_email", table_name="org_invitations")
    op.drop_index(
        "idx_notifications_user_org_channel_read_archived",
        table_name="notifications",
    )
    op.drop_index(
        "idx_org_feature_flags_org_key",
        table_name="org_feature_flags",
    )
    op.drop_index(
        "idx_org_usage_records_org_metric_recorded",
        table_name="org_usage_records",
    )
