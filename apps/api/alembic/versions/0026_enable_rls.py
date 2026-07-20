"""Enable Row Level Security (RLS) on tenant-scoped tables.

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_SCOPED_TABLES = [
    "organizations",
    "users",
    "team_members",
    "campaigns",
    "content",
    "content_templates",
    "brand_voices",
    "ad_accounts",
    "ad_campaigns",
    "ad_creatives",
    "ad_insights",
    "email_providers",
    "email_campaigns",
    "email_events",
    "workflows",
    "workflow_executions",
    "automation_rules",
    "audience_segments",
    "bid_optimization_rules",
    "budget_allocation_rules",
    "campaign_budgets",
    "campaign_templates",
    "ab_tests",
    "ab_test_variants",
    "content_publishes",
    "content_recommendations",
    "dashboards",
    "dashboard_widgets",
    "report_schedules",
    "report_templates",
    "report_delivery_logs",
    "notifications",
    "notification_templates",
    "broadcast_announcements",
    "user_notification_preferences",
    "system_prompts",
    "knowledge_nodes",
    "knowledge_relations",
    "memories",
    "job_records",
    "org_billing_plans",
    "org_feature_flags",
    "org_invitations",
    "org_usage_records",
]


def upgrade() -> None:
    # Enable RLS on all tenant-scoped tables
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # Create policy function for tenant isolation
    op.execute("""
        CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
        SELECT current_setting('app.current_tenant_id', true)::UUID
        $$ LANGUAGE sql STABLE SECURITY DEFINER;
    """)

    # Create default policies for tenant-scoped tables
    for table in TENANT_SCOPED_TABLES:
        # Check if table has tenant_id or organization_id column
        # Use a safe approach with parameterized queries
        safe_table = table.replace("-", "_").replace(";", "")  # Basic sanitization
        op.execute(
            sa.text("""
            DO $$
            BEGIN
                -- Check for tenant_id column
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = 'tenant_id'
                ) THEN
                    EXECUTE format(
                        'CREATE POLICY tenant_isolation ON %I USING (tenant_id = current_tenant_id())',
                        safe_table
                    );
                -- Check for organization_id column
                ELSIF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = 'organization_id'
                ) THEN
                    EXECUTE format(
                        'CREATE POLICY tenant_isolation ON %I USING (organization_id = current_tenant_id())',
                        safe_table
                    );
                -- Check for org_id column
                ELSIF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = 'org_id'
                ) THEN
                    EXECUTE format(
                        'CREATE POLICY tenant_isolation ON %I USING (org_id = current_tenant_id())',
                        safe_table
                    );
                END IF;
            END $$;
        """),
            {"table_name": safe_table},
        )

    # Special handling for audit_logs (partitioned table)
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY audit_logs_tenant_isolation ON audit_logs USING (tenant_id = current_tenant_id())"
    )

    # Special handling for outbox table
    op.execute("ALTER TABLE outbox ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY outbox_tenant_isolation ON outbox USING (true)"
    )  # Outbox is tenant-agnostic; access controlled at app layer

    # Special handling for embeddings table
    op.execute("ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY embeddings_tenant_isolation ON embeddings USING (tenant_id = current_tenant_id())"
    )


def downgrade() -> None:
    # Drop all RLS policies
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop special table policies
    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS outbox_tenant_isolation ON outbox")
    op.execute("ALTER TABLE outbox DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS embeddings_tenant_isolation ON embeddings")
    op.execute("ALTER TABLE embeddings DISABLE ROW LEVEL SECURITY")

    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS current_tenant_id()")
