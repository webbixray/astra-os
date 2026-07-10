"""Add missing foreign key constraints, unique constraints, and composite indexes

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # noqa: PLR0915
    # Organizations (self-referential)  # noqa: ERA001
    op.create_foreign_key(
        "fk_organizations_parent_org",
        "organizations",
        "organizations",
        ["parent_org_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Team members
    op.create_foreign_key(
        "fk_team_members_organization",
        "team_members",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_team_members_user",
        "team_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Org invitations
    op.create_foreign_key(
        "fk_org_invitations_organization",
        "org_invitations",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_org_invitations_invited_by",
        "org_invitations",
        "users",
        ["invited_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Billing plan
    op.create_foreign_key(
        "fk_billing_plan_organization",
        "org_billing_plans",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Usage records
    op.create_foreign_key(
        "fk_usage_record_organization",
        "org_usage_records",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Feature flags
    op.create_foreign_key(
        "fk_feature_flag_organization",
        "org_feature_flags",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Report templates
    op.create_foreign_key(
        "fk_report_template_organization",
        "report_templates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_report_template_created_by",
        "report_templates",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Report delivery logs
    op.create_foreign_key(
        "fk_report_delivery_log_organization",
        "report_delivery_logs",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_report_delivery_log_template",
        "report_delivery_logs",
        "report_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_report_delivery_log_schedule",
        "report_delivery_logs",
        "report_schedules",
        ["schedule_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Report schedules
    op.create_foreign_key(
        "fk_report_schedule_organization",
        "report_schedules",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_report_schedule_created_by",
        "report_schedules",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Campaigns
    op.create_foreign_key(
        "fk_campaigns_organization",
        "campaigns",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_campaigns_created_by",
        "campaigns",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Campaign budgets
    op.create_foreign_key(
        "fk_campaign_budget_campaign",
        "campaign_budgets",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Campaign templates
    op.create_foreign_key(
        "fk_campaign_template_organization",
        "campaign_templates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_campaign_template_created_by",
        "campaign_templates",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # AB tests
    op.create_foreign_key(
        "fk_ab_tests_campaign",
        "ab_tests",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_ab_tests_organization",
        "ab_tests",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_ab_tests_created_by",
        "ab_tests",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # AB test variants
    op.create_foreign_key(
        "fk_ab_test_variants_ab_test",
        "ab_test_variants",
        "ab_tests",
        ["ab_test_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # AB tests -> winner variant (deferred, self-referential through variants)
    op.create_foreign_key(
        "fk_ab_tests_winner_variant",
        "ab_tests",
        "ab_test_variants",
        ["winner_variant_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Automation tables
    op.create_foreign_key(
        "fk_budget_allocation_rule_organization",
        "budget_allocation_rules",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_budget_allocation_rule_campaign",
        "budget_allocation_rules",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_bid_optimization_rule_organization",
        "bid_optimization_rules",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_bid_optimization_rule_ad_account",
        "bid_optimization_rules",
        "ad_accounts",
        ["ad_account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_audience_segment_organization",
        "audience_segments",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_content_recommendation_organization",
        "content_recommendations",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_content_recommendation_campaign",
        "content_recommendations",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_automation_rule_organization",
        "automation_rules",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_automation_rule_created_by",
        "automation_rules",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Content
    op.create_foreign_key(
        "fk_content_campaign",
        "content",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_content_organization",
        "content",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_content_brand_profile",
        "content",
        "brand_voices",
        ["brand_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_content_created_by",
        "content",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Content templates
    op.create_foreign_key(
        "fk_content_template_organization",
        "content_templates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_content_template_created_by",
        "content_templates",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Content publishes
    op.create_foreign_key(
        "fk_content_publish_content",
        "content_publishes",
        "content",
        ["content_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Brand voices
    op.create_foreign_key(
        "fk_brand_voice_organization",
        "brand_voices",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_brand_voice_created_by",
        "brand_voices",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Dashboards
    op.create_foreign_key(
        "fk_dashboards_organization",
        "dashboards",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_dashboards_created_by",
        "dashboards",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Dashboard widgets
    op.create_foreign_key(
        "fk_dashboard_widgets_dashboard",
        "dashboard_widgets",
        "dashboards",
        ["dashboard_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Email campaigns
    op.create_foreign_key(
        "fk_email_campaigns_organization",
        "email_campaigns",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_email_campaigns_provider",
        "email_campaigns",
        "email_providers",
        ["provider_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_email_campaigns_created_by",
        "email_campaigns",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Email events
    op.create_foreign_key(
        "fk_email_events_campaign",
        "email_events",
        "email_campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Email providers
    op.create_foreign_key(
        "fk_email_providers_organization",
        "email_providers",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_email_providers_created_by",
        "email_providers",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Ad campaigns (missing created_by FK)
    op.create_foreign_key(
        "fk_ad_campaigns_created_by",
        "ad_campaigns",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Ad creatives (missing created_by FK)
    op.create_foreign_key(
        "fk_ad_creatives_created_by",
        "ad_creatives",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Workflows (missing created_by FK)
    op.create_foreign_key(
        "fk_workflows_created_by",
        "workflows",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Workflow executions (missing triggered_by FK)
    op.create_foreign_key(
        "fk_workflow_executions_triggered_by",
        "workflow_executions",
        "users",
        ["triggered_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Audit logs
    op.create_foreign_key(
        "fk_audit_logs_organization",
        "audit_logs",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_audit_logs_user",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Job records
    op.create_foreign_key(
        "fk_job_records_organization",
        "job_records",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # API usage records
    op.create_foreign_key(
        "fk_api_usage_records_organization",
        "api_usage_records",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_api_usage_records_user",
        "api_usage_records",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Notifications
    op.create_foreign_key(
        "fk_notifications_organization",
        "notifications",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notifications_user",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notifications_template",
        "notifications",
        "notification_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Notification templates
    op.create_foreign_key(
        "fk_notification_templates_organization",
        "notification_templates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Broadcast announcements
    op.create_foreign_key(
        "fk_broadcast_announcements_organization",
        "broadcast_announcements",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_broadcast_announcements_created_by",
        "broadcast_announcements",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # User notification preferences
    op.create_foreign_key(
        "fk_user_notification_preferences_user",
        "user_notification_preferences",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # System prompts
    op.create_foreign_key(
        "fk_system_prompts_org",
        "system_prompts",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_system_prompts_created_by",
        "system_prompts",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Unique Constraints

    # Feature flags: one flag per org per key
    op.create_unique_constraint(
        "uq_feature_flags_org_key",
        "org_feature_flags",
        ["organization_id", "feature_key"],
    )

    # Campaign budgets: one budget per campaign
    op.create_unique_constraint(
        "uq_campaign_budget_campaign",
        "campaign_budgets",
        ["campaign_id"],
    )

    # Notification preferences: one preference per user per type per channel
    op.create_unique_constraint(
        "uq_notification_preferences_user_type_channel",
        "user_notification_preferences",
        ["user_id", "notification_type", "channel"],
    )

    # Report templates: unique name per org
    op.create_unique_constraint(
        "uq_report_templates_org_name",
        "report_templates",
        ["organization_id", "name"],
    )

    # Composite Indexes

    # Email events: query by campaign + event type
    op.create_index(
        "idx_email_events_campaign_type",
        "email_events",
        ["campaign_id", "event_type"],
    )

    # Email campaigns: query by org + status
    op.create_index(
        "idx_email_campaigns_org_status",
        "email_campaigns",
        ["organization_id", "status"],
    )

    # API usage records: time-range queries
    op.create_index(
        "idx_api_usage_records_org_created",
        "api_usage_records",
        ["organization_id", "created_at"],
    )

    # API usage records: endpoint stats
    op.create_index(
        "idx_api_usage_records_endpoint_method",
        "api_usage_records",
        ["endpoint", "method"],
    )

    # Job records: query by org + status
    op.create_index(
        "idx_job_records_org_status",
        "job_records",
        ["organization_id", "status"],
    )

    # Job records: query by org + job type
    op.create_index(
        "idx_job_records_org_type",
        "job_records",
        ["organization_id", "job_type"],
    )

    # Audit logs: time-range queries
    op.create_index(
        "idx_audit_logs_org_created",
        "audit_logs",
        ["organization_id", "created_at"],
    )

    # Dashboard widgets: position-based ordering
    op.create_index(
        "idx_dashboard_widgets_dashboard_position",
        "dashboard_widgets",
        ["dashboard_id", "pos_y", "pos_x"],
    )


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index("idx_dashboard_widgets_dashboard_position", table_name="dashboard_widgets")
    op.drop_index("idx_audit_logs_org_created", table_name="audit_logs")
    op.drop_index("idx_job_records_org_type", table_name="job_records")
    op.drop_index("idx_job_records_org_status", table_name="job_records")
    op.drop_index("idx_api_usage_records_endpoint_method", table_name="api_usage_records")
    op.drop_index("idx_api_usage_records_org_created", table_name="api_usage_records")
    op.drop_index("idx_email_campaigns_org_status", table_name="email_campaigns")
    op.drop_index("idx_email_events_campaign_type", table_name="email_events")

    # Drop unique constraints
    op.drop_constraint("uq_report_templates_org_name", "report_templates", type_="unique")
    op.drop_constraint("uq_notification_preferences_user_type_channel", "user_notification_preferences", type_="unique")
    op.drop_constraint("uq_campaign_budget_campaign", "campaign_budgets", type_="unique")
    op.drop_constraint("uq_feature_flags_org_key", "org_feature_flags", type_="unique")

    # Drop foreign keys (in reverse order)
    fk_drops = [
        ("system_prompts", "fk_system_prompts_created_by"),
        ("system_prompts", "fk_system_prompts_org"),
        ("user_notification_preferences", "fk_user_notification_preferences_user"),
        ("broadcast_announcements", "fk_broadcast_announcements_created_by"),
        ("broadcast_announcements", "fk_broadcast_announcements_organization"),
        ("notification_templates", "fk_notification_templates_organization"),
        ("notifications", "fk_notifications_template"),
        ("notifications", "fk_notifications_user"),
        ("notifications", "fk_notifications_organization"),
        ("api_usage_records", "fk_api_usage_records_user"),
        ("api_usage_records", "fk_api_usage_records_organization"),
        ("job_records", "fk_job_records_organization"),
        ("audit_logs", "fk_audit_logs_user"),
        ("audit_logs", "fk_audit_logs_organization"),
        ("workflow_executions", "fk_workflow_executions_triggered_by"),
        ("workflows", "fk_workflows_created_by"),
        ("ad_creatives", "fk_ad_creatives_created_by"),
        ("ad_campaigns", "fk_ad_campaigns_created_by"),
        ("email_providers", "fk_email_providers_created_by"),
        ("email_providers", "fk_email_providers_organization"),
        ("email_events", "fk_email_events_campaign"),
        ("email_campaigns", "fk_email_campaigns_created_by"),
        ("email_campaigns", "fk_email_campaigns_provider"),
        ("email_campaigns", "fk_email_campaigns_organization"),
        ("dashboard_widgets", "fk_dashboard_widgets_dashboard"),
        ("dashboards", "fk_dashboards_created_by"),
        ("dashboards", "fk_dashboards_organization"),
        ("brand_voices", "fk_brand_voice_created_by"),
        ("brand_voices", "fk_brand_voice_organization"),
        ("content_publishes", "fk_content_publish_content"),
        ("content_templates", "fk_content_template_created_by"),
        ("content_templates", "fk_content_template_organization"),
        ("content", "fk_content_created_by"),
        ("content", "fk_content_brand_profile"),
        ("content", "fk_content_organization"),
        ("content", "fk_content_campaign"),
        ("automation_rules", "fk_automation_rule_created_by"),
        ("automation_rules", "fk_automation_rule_organization"),
        ("content_recommendations", "fk_content_recommendation_campaign"),
        ("content_recommendations", "fk_content_recommendation_organization"),
        ("audience_segments", "fk_audience_segment_organization"),
        ("bid_optimization_rules", "fk_bid_optimization_rule_ad_account"),
        ("bid_optimization_rules", "fk_bid_optimization_rule_organization"),
        ("budget_allocation_rules", "fk_budget_allocation_rule_campaign"),
        ("budget_allocation_rules", "fk_budget_allocation_rule_organization"),
        ("ab_tests", "fk_ab_tests_winner_variant"),
        ("ab_test_variants", "fk_ab_test_variants_ab_test"),
        ("ab_tests", "fk_ab_tests_created_by"),
        ("ab_tests", "fk_ab_tests_organization"),
        ("ab_tests", "fk_ab_tests_campaign"),
        ("campaign_templates", "fk_campaign_template_created_by"),
        ("campaign_templates", "fk_campaign_template_organization"),
        ("campaign_budgets", "fk_campaign_budget_campaign"),
        ("campaigns", "fk_campaigns_created_by"),
        ("campaigns", "fk_campaigns_organization"),
        ("report_schedules", "fk_report_schedule_created_by"),
        ("report_schedules", "fk_report_schedule_organization"),
        ("report_delivery_logs", "fk_report_delivery_log_schedule"),
        ("report_delivery_logs", "fk_report_delivery_log_template"),
        ("report_delivery_logs", "fk_report_delivery_log_organization"),
        ("report_templates", "fk_report_template_created_by"),
        ("report_templates", "fk_report_template_organization"),
        ("org_feature_flags", "fk_feature_flag_organization"),
        ("org_usage_records", "fk_usage_record_organization"),
        ("org_billing_plans", "fk_billing_plan_organization"),
        ("org_invitations", "fk_org_invitations_invited_by"),
        ("org_invitations", "fk_org_invitations_organization"),
        ("team_members", "fk_team_members_user"),
        ("team_members", "fk_team_members_organization"),
        ("organizations", "fk_organizations_parent_org"),
    ]

    for table, constraint_name in fk_drops:
        op.drop_constraint(constraint_name, table, type_="foreignkey")
