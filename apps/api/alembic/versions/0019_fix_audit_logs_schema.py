"""Fix audit_logs schema conflict between 0006 and 0018

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
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
            sa.Column("organization_id", UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("user_id", UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("action", sa.String(50), nullable=False, index=True),
            sa.Column("resource_type", sa.String(50), nullable=False),
            sa.Column("resource_id", sa.String(255), server_default="", nullable=False),
            sa.Column("details", JSONB, server_default="{}", nullable=False),
            sa.Column("ip_address", sa.String(45), server_default="", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        return

    columns = [col["name"] for col in inspector.get_columns("audit_logs")]

    has_old_schema = "actor_id" in columns or "metadata" in columns

    if not has_old_schema:
        return

    if "user_id" not in columns:
        op.add_column(
            "audit_logs",
            sa.Column("user_id", UUID(as_uuid=True), nullable=True, index=True),
        )

    if "details" not in columns:
        op.add_column(
            "audit_logs",
            sa.Column("details", JSONB, nullable=True),
        )

    if "ip_address" not in columns:
        op.add_column(
            "audit_logs",
            sa.Column("ip_address", sa.String(45), server_default="", nullable=True),
        )

    bind = op.get_bind()
    if "actor_id" in columns:
        bind.execute(
            text("UPDATE audit_logs SET user_id = actor_id WHERE actor_id IS NOT NULL")
        )
    if "metadata" in columns:
        bind.execute(
            text("UPDATE audit_logs SET details = metadata")
        )
    if "ip_address" not in columns:
        bind.execute(
            text("UPDATE audit_logs SET ip_address = '' WHERE ip_address IS NULL")
        )

    if "actor_id" in columns:
        op.drop_column("audit_logs", "actor_id")

    if "metadata" in columns:
        op.drop_column("audit_logs", "metadata")

    op.alter_column(
        "audit_logs", "action",
        type_=sa.String(50),
        existing_type=sa.String(100),
        postgresql_using="action::varchar(50)",
    )
    op.alter_column(
        "audit_logs", "resource_type",
        type_=sa.String(50),
        existing_type=sa.String(100),
        postgresql_using="resource_type::varchar(50)",
    )

    if "details" not in columns:
        op.alter_column(
            "audit_logs", "details",
            nullable=False,
            server_default="{}",
            existing_type=JSONB,
        )

    op.alter_column(
        "audit_logs", "ip_address",
        nullable=False,
        server_default="",
        existing_type=sa.String(45),
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("audit_logs")]

    if "user_id" in columns:
        op.add_column(
            "audit_logs",
            sa.Column("actor_id", UUID(as_uuid=True), nullable=True, index=True),
        )
        bind = op.get_bind()
        bind.execute(
            text("UPDATE audit_logs SET actor_id = user_id WHERE user_id IS NOT NULL")
        )

    if "details" in columns:
        op.add_column(
            "audit_logs",
            sa.Column("metadata", JSONB, server_default="{}", nullable=False),
        )
        bind = op.get_bind()
        bind.execute(
            text("UPDATE audit_logs SET metadata = details")
        )

    if "user_id" in columns:
        op.drop_column("audit_logs", "user_id")
    if "details" in columns:
        op.drop_column("audit_logs", "details")
    if "ip_address" in columns:
        op.drop_column("audit_logs", "ip_address")

    op.alter_column(
        "audit_logs", "action",
        type_=sa.String(100),
        existing_type=sa.String(50),
        postgresql_using="action::varchar(100)",
    )
    op.alter_column(
        "audit_logs", "resource_type",
        type_=sa.String(100),
        existing_type=sa.String(50),
        postgresql_using="resource_type::varchar(100)",
    )
