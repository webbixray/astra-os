"""Create system_prompts table for versioned prompt management

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_prompts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("variables", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
        sa.Column("is_builtin", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_system_prompts_name_org",
        "system_prompts",
        ["name", "org_id"],
        unique=True,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_system_prompts_category_status",
        "system_prompts",
        ["category", "status"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("idx_system_prompts_name_org", table_name="system_prompts")
    op.drop_index("idx_system_prompts_category_status", table_name="system_prompts")
    op.drop_table("system_prompts")
