"""Add notification hub tables and enhance notifications

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # New tables
    op.create_table(
        "notification_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("title_template", sa.String(255), nullable=False),
        sa.Column("body_template", sa.Text, server_default="", nullable=False),
        sa.Column("variables", ARRAY(sa.String), default=list, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_notification_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "broadcast_announcements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, server_default="", nullable=False),
        sa.Column("severity", sa.String(20), server_default="info", nullable=False),
        sa.Column("target_role", sa.String(50), server_default="", nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("dismissed_by", ARRAY(UUID(as_uuid=True)), default=list, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Enhance notifications table
    op.add_column("notifications", sa.Column("channel", sa.String(20), server_default="in_app", nullable=False))
    op.add_column("notifications", sa.Column("template_id", UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("archived", sa.Boolean, server_default="false", nullable=False, index=True))


def downgrade() -> None:
    op.drop_column("notifications", "archived")
    op.drop_column("notifications", "read_at")
    op.drop_column("notifications", "template_id")
    op.drop_column("notifications", "channel")

    op.drop_table("broadcast_announcements")
    op.drop_table("user_notification_preferences")
    op.drop_table("notification_templates")
