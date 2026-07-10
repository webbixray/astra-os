"""Add dashboards and dashboard_widgets tables

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("layout_columns", sa.Integer, default=12, nullable=False),
        sa.Column("is_default", sa.Boolean, default=False, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dashboard_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("widget_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("pos_x", sa.Integer, default=0, nullable=False),
        sa.Column("pos_y", sa.Integer, default=0, nullable=False),
        sa.Column("width", sa.Integer, default=1, nullable=False),
        sa.Column("height", sa.Integer, default=1, nullable=False),
        sa.Column("config", JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("dashboard_widgets")
    op.drop_table("dashboards")
