"""Add system monitoring tables

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    table_names = inspector.get_table_names()

    if "audit_logs" not in table_names:
        op.create_table(
            "audit_logs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("action", sa.String(50), nullable=False, index=True),
            sa.Column("resource_type", sa.String(50), nullable=False),
            sa.Column("resource_id", sa.String(255), server_default="", nullable=False),
            sa.Column("details", JSONB, default=dict, nullable=False),
            sa.Column("ip_address", sa.String(45), server_default="", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    op.create_table(
        "job_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("job_type", sa.String(100), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, index=True),
        sa.Column("payload", JSONB, default=dict, nullable=False),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, server_default="", nullable=False),
        sa.Column("retry_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer, server_default="3", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "api_usage_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("ip_address", sa.String(45), server_default="", nullable=False),
        sa.Column("response_time_ms", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("api_usage_records")
    op.drop_table("job_records")
    op.drop_table("audit_logs")
