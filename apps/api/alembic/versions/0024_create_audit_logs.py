"""Alter audit_logs to new audit schema.

Drops action/resource_type/resource_id columns, adds event_type/entity_type/entity_id,
and adjusts nullability on organization_id, details, ip_address.

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
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
            sa.Column("event_type", sa.String(100), nullable=False, index=True),
            sa.Column("entity_type", sa.String(100), nullable=False, index=True),
            sa.Column("entity_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("details", sa.JSON, nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        return

    columns = {col["name"] for col in inspector.get_columns("audit_logs")}

    if "action" in columns:
        op.drop_column("audit_logs", "action")
    if "resource_type" in columns:
        op.drop_column("audit_logs", "resource_type")
    if "resource_id" in columns:
        op.drop_column("audit_logs", "resource_id")

    if "event_type" not in columns:
        op.add_column("audit_logs", sa.Column("event_type", sa.String(100), nullable=False))
        op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])

    if "entity_type" not in columns:
        op.add_column("audit_logs", sa.Column("entity_type", sa.String(100), nullable=False))
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])

    if "entity_id" not in columns:
        op.add_column("audit_logs", sa.Column("entity_id", UUID(as_uuid=True), nullable=False))
        op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])

    if "organization_id" in columns:
        org_col = [c for c in inspector.get_columns("audit_logs") if c["name"] == "organization_id"][0]
        if not org_col["nullable"]:
            op.alter_column("audit_logs", "organization_id", nullable=True)

    if "details" in columns:
        details_col = [c for c in inspector.get_columns("audit_logs") if c["name"] == "details"][0]
        if details_col["nullable"] is False:
            op.alter_column("audit_logs", "details", nullable=True)

    if "ip_address" in columns:
        ip_col = [c for c in inspector.get_columns("audit_logs") if c["name"] == "ip_address"][0]
        if not ip_col["nullable"]:
            op.alter_column("audit_logs", "ip_address", nullable=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("audit_logs")}

    if "event_type" in columns:
        op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
        op.drop_column("audit_logs", "event_type")
    if "entity_type" in columns:
        op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
        op.drop_column("audit_logs", "entity_type")
    if "entity_id" in columns:
        op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
        op.drop_column("audit_logs", "entity_id")

    op.add_column("audit_logs", sa.Column("action", sa.String(50), nullable=False, index=True))
    op.add_column("audit_logs", sa.Column("resource_type", sa.String(50), nullable=False))
    op.add_column("audit_logs", sa.Column("resource_id", sa.String(255), server_default="", nullable=False))

    op.alter_column("audit_logs", "organization_id", nullable=False)
    op.alter_column("audit_logs", "ip_address", nullable=False, server_default="")
