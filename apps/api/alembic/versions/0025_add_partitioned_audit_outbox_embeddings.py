"""Add partitioned audit_logs, outbox, and embeddings tables.

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-11
"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop existing non-partitioned audit_logs table and related objects
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")

    # Create partitioned audit_logs table (partitioned by month on created_at)
    op.execute("""
        CREATE TABLE audit_logs (
            id BIGSERIAL NOT NULL,
            tenant_id UUID NOT NULL,
            user_id UUID,
            agent_id UUID,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            resource_id UUID,
            before JSONB,
            after JSONB,
            metadata JSONB NOT NULL DEFAULT '{}',
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (tenant_id, created_at, id)
        ) PARTITION BY RANGE (created_at)
    """)

    # Create monthly partitions for the next 2 years (proper calendar months)
    for year in range(2026, 2028):
        for month in range(1, 13):
            partition_name = f"audit_logs_y{year}m{month:02d}"

            # Calculate partition start and end dates (first day of month to first day of next month)
            if month == 12:
                next_year = year + 1
                next_month = 1
            else:
                next_year = year
                next_month = month + 1

            partition_start = date(year, month, 1)
            partition_end = date(next_year, next_month, 1)

            op.execute(f"""
                CREATE TABLE audit_logs_y{year}m{month:02d} PARTITION OF audit_logs
                FOR VALUES FROM ('{partition_start.isoformat()}') TO ('{partition_end.isoformat()}')
            """)

            # Create indexes on each partition
            op.execute(f"""
                CREATE INDEX ix_audit_logs_y{year}m{month:02d}_tenant_user
                ON audit_logs_y{year}m{month:02d} (tenant_id, user_id, created_at DESC)
            """)
            op.execute(f"""
                CREATE INDEX ix_audit_logs_y{year}m{month:02d}_entity
                ON audit_logs_y{year}m{month:02d} (resource_type, resource_id)
            """)
            op.execute(f"""
                CREATE INDEX ix_audit_logs_y{year}m{month:02d}_action_created
                ON audit_logs_y{year}m{month:02d} (action, created_at DESC)
            """)

    # Create default partition for any data outside the defined ranges
    op.execute("""
        CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT
    """)

    # Create outbox table for reliable event publishing
    op.create_table(
        "outbox",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("aggregate_type", sa.String(100), nullable=False),
        sa.Column("aggregate_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_unpublished", "outbox", ["created_at"], postgresql_where=sa.text("published_at IS NULL"))

    # Create embeddings table - check pgvector availability first
    # Use a separate connection to check pgvector availability
    conn = op.get_bind()
    try:
        result = conn.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        vector_available = result.scalar() is not None
    except Exception:
        vector_available = False

    # Create embeddings table with vector support if available
    if vector_available:
        op.create_table(
            "embeddings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("source_type", sa.String(50), nullable=False),
            sa.Column("source_id", UUID(as_uuid=True), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("embedding", sa.dialects.postgresql.VECTOR(1536), nullable=True),
            sa.Column("metadata", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_embeddings_tenant_source", "embeddings", ["tenant_id", "source_type", "source_id"])
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_embeddings_vector
            ON embeddings USING hnsw (embedding vector_cosine_ops)
        """)
    else:
        # Fallback: store embeddings as arrays
        op.create_table(
            "embeddings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("source_type", sa.String(50), nullable=False),
            sa.Column("source_id", UUID(as_uuid=True), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("embedding", sa.dialects.postgresql.ARRAY(sa.Float), nullable=True),
            sa.Column("metadata", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_embeddings_tenant_source", "embeddings", ["tenant_id", "source_type", "source_id"])


def downgrade() -> None:
    # Drop partitions first
    for year in range(2026, 2028):
        for month in range(1, 13):
            partition_name = f"audit_logs_y{year}m{month:02d}"
            op.execute(f"DROP TABLE IF EXISTS {partition_name}")

    op.execute("DROP TABLE IF EXISTS audit_logs_default")
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS outbox")
    op.execute("DROP TABLE IF EXISTS embeddings")