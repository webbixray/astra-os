"""Add report templates and delivery logs

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, default="", nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("config", JSONB, default=dict, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "report_delivery_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("template_id", UUID(as_uuid=True), nullable=True),
        sa.Column("schedule_id", UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("format", sa.String(20), default="csv", nullable=False),
        sa.Column("channel", sa.String(50), default="download", nullable=False),
        sa.Column("recipient", sa.String(255), default="", nullable=False),
        sa.Column("status", sa.String(50), default="pending", nullable=False, index=True),
        sa.Column("error_message", sa.Text, default="", nullable=False),
        sa.Column("file_url", sa.String(500), default="", nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("report_delivery_logs")
    op.drop_table("report_templates")
