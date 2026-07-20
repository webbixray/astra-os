"""Add agent orchestrator tables: agent_memories, agent_events, agent_traces.

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # agent_memories — working / episodic / semantic memory store
    # ---------------------------------------------------------------
    op.create_table(
        "agent_memories",
        sa.Column("memory_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "memory_type",
            sa.String(20),
            nullable=False,
            index=True,
            comment="working | episodic | semantic",
        ),
        sa.Column("key", sa.String(500), nullable=False),
        sa.Column("value", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "embedding",
            Vector(1536),
            nullable=True,
        ),
        sa.Column(
            "importance",
            sa.Float,
            nullable=False,
            server_default="0.5",
        ),
        sa.Column("tags", JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "access_count",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_agent_memories_tenant_agent_type",
        "agent_memories",
        ["tenant_id", "agent_id", "memory_type"],
    )
    op.create_index(
        "ix_agent_memories_tenant_importance",
        "agent_memories",
        ["tenant_id", "importance"],
    )

    # HNSW index for vector similarity search (if pgvector available)
    conn = op.get_bind()
    try:
        result = conn.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        vector_available = result.scalar() is not None
    except Exception:
        vector_available = False

    if vector_available:
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_agent_memories_embedding
            ON agent_memories USING hnsw (embedding vector_cosine_ops)
        """)

    # ---------------------------------------------------------------
    # agent_events — persistent event store for agent actions
    # ---------------------------------------------------------------
    op.create_table(
        "agent_events",
        sa.Column("event_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("source", sa.String(100), nullable=False, index=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("correlation_id", UUID(as_uuid=True), nullable=True, index=True),
    )

    op.create_index(
        "ix_agent_events_tenant_type_time",
        "agent_events",
        ["tenant_id", "event_type", "timestamp"],
    )

    # ---------------------------------------------------------------
    # agent_traces — reasoning trace / audit trail for agent actions
    # ---------------------------------------------------------------
    op.create_table(
        "agent_traces",
        sa.Column("trace_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("task_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("parent_trace_id", UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("iteration", sa.Integer, nullable=False, server_default="0"),
        sa.Column("thought", sa.Text, nullable=True, comment="Agent reasoning at this step"),
        sa.Column(
            "action", sa.String(200), nullable=True, comment="Tool or delegation action taken"
        ),
        sa.Column("action_input", JSONB, nullable=True),
        sa.Column("observation", sa.Text, nullable=True, comment="Result of the action"),
        sa.Column(
            "final_answer", sa.Text, nullable=True, comment="Final output if this is terminal"
        ),
        sa.Column("tool_calls", JSONB, nullable=False, server_default="[]"),
        sa.Column("tool_results", JSONB, nullable=False, server_default="[]"),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_index(
        "ix_agent_traces_tenant_agent",
        "agent_traces",
        ["tenant_id", "agent_id", "created_at"],
    )
    op.create_index(
        "ix_agent_traces_tenant_task",
        "agent_traces",
        ["tenant_id", "task_id"],
    )

    # ---------------------------------------------------------------
    # Enable RLS on new tables
    # ---------------------------------------------------------------
    for table in ("agent_memories", "agent_events", "agent_traces"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            f"USING (tenant_id = current_tenant_id())"
        )


def downgrade() -> None:
    # Drop RLS policies
    for table in ("agent_memories", "agent_events", "agent_traces"):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("agent_traces")
    op.drop_table("agent_events")
    op.drop_table("agent_memories")
