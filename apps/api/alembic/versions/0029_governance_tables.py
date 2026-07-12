"""Create governance tables — approval rules, requests, decisions, autonomy, agent actions.

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0029"
down_revision: str = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── approval_rules ──────────────────────────────────────────────────
    op.create_table(
        "approval_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True, server_default=""),
        sa.Column("trigger", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("conditions", sa.JSON, nullable=True),
        sa.Column("approver_roles", sa.JSON, nullable=True),
        sa.Column("approver_users", sa.JSON, nullable=True),
        sa.Column("escalation_users", sa.JSON, nullable=True),
        sa.Column("approval_timeout_hours", sa.Integer, nullable=False, server_default=sa.text("24")),
        sa.Column("auto_reject_on_timeout", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_approval_rules_organization_id",
        "approval_rules",
        ["organization_id"],
    )
    op.create_index(
        "ix_approval_rules_trigger",
        "approval_rules",
        ["trigger"],
    )

    # ── approval_requests ───────────────────────────────────────────────
    op.create_table(
        "approval_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("rule_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("rule_name", sa.String(255), nullable=True, server_default=""),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("action_resource_id", sa.String(255), nullable=True, server_default=""),
        sa.Column("action_resource_type", sa.String(100), nullable=True, server_default=""),
        sa.Column("action_context", sa.JSON, nullable=True),
        sa.Column("action_summary", sa.String(1000), nullable=True, server_default=""),
        sa.Column("triggered_by_agent_id", sa.String(255), nullable=True),
        sa.Column("triggered_by_agent_type", sa.String(100), nullable=True),
        sa.Column("triggered_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("assigned_to", UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_role", sa.String(50), nullable=True, server_default=""),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_approval_requests_status",
        "approval_requests",
        ["status"],
    )

    # ── approval_decisions ──────────────────────────────────────────────
    op.create_table(
        "approval_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=True, server_default=""),
        sa.Column("conditions", sa.JSON, nullable=True),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── autonomy_configs ────────────────────────────────────────────────
    op.create_table(
        "autonomy_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("default_level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("agent_levels", sa.JSON, nullable=True),
        sa.Column("action_overrides", sa.JSON, nullable=True),
        sa.Column("auto_approve_spend_limit", sa.Float, nullable=False, server_default=sa.text("100.0")),
        sa.Column("auto_approve_currency", sa.String(10), nullable=False, server_default="'USD'"),
        sa.Column("auto_execute_channels", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── agent_actions ───────────────────────────────────────────────────
    op.create_table(
        "agent_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True, server_default=""),
        sa.Column("resource_id", sa.String(255), nullable=True, server_default=""),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("reasoning", sa.String(5000), nullable=True, server_default=""),
        sa.Column("reasoning_trace", sa.JSON, nullable=True),
        sa.Column("autonomy_level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("was_auto_executed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("approval_request_id", UUID(as_uuid=True), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("error_message", sa.String(1000), nullable=True, server_default=""),
        sa.Column("result", sa.JSON, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("model_used", sa.String(100), nullable=True, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_agent_actions_agent_id",
        "agent_actions",
        ["agent_id"],
    )
    op.create_index(
        "ix_agent_actions_agent_type",
        "agent_actions",
        ["agent_type"],
    )
    op.create_index(
        "ix_agent_actions_action",
        "agent_actions",
        ["action"],
    )
    op.create_index(
        "ix_agent_actions_created_at",
        "agent_actions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("agent_actions")
    op.drop_table("autonomy_configs")
    op.drop_table("approval_decisions")
    op.drop_table("approval_requests")
    op.drop_table("approval_rules")
