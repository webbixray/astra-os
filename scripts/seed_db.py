"""
Database seed script for development environment.

Usage:
    cd apps/api
    python -m scripts.seed_db

This script creates sample data for development and testing.
It is safe to run multiple times - it will skip existing data.
"""

import asyncio
import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.infrastructure.auth.password import hash_password
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.content.content_model import ContentModel
from app.infrastructure.db.models.notifications.notification_model import NotificationModel
from app.infrastructure.db.models.organization import OrganizationModel
from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.workflows.workflow_model import WorkflowModel
from app.infrastructure.db.session import create_session_factory

# ---------------------------------------------------------------------------
# Seed constants
# ---------------------------------------------------------------------------

SEED_EMAIL = "admin@astra.dev"
SEED_PASSWORD = "AstraAdmin1!"

USERS_DATA = [
    {
        "email": "admin@astra.dev",
        "name": "Astra Admin",
        "is_active": True,
    },
    {
        "email": "sarah@acmecorp.com",
        "name": "Sarah Chen",
        "is_active": True,
    },
    {
        "email": "mike@acmecorp.com",
        "name": "Mike Johnson",
        "is_active": True,
    },
]

ORGANIZATIONS_DATA = [
    {
        "name": "Astra Demo Organization",
        "slug": "astra-demo",
        "plan_tier": "professional",
        "settings": {"timezone": "America/New_York", "default_currency": "USD"},
    },
    {
        "name": "Acme Corp",
        "slug": "acme-corp",
        "plan_tier": "enterprise",
        "settings": {"timezone": "America/Los_Angeles", "default_currency": "USD"},
    },
]

# team_members_data references users/orgs by index – filled at seed time
TEAM_MEMBERS_DATA = [
    # (user_index, org_index, role, permissions)
    (0, 0, "owner", ["campaigns:manage", "content:manage", "workflows:manage", "team:manage"]),
    (1, 1, "admin", ["campaigns:manage", "content:manage", "workflows:manage"]),
    (2, 1, "operator", ["campaigns:view", "content:edit"]),
]

CAMPAIGNS_DATA = [
    # --- Astra Demo campaigns (org_index 0) ---
    {
        "org_index": 0,
        "name": "Q1 Product Launch",
        "status": "active",
        "objective": "product_launch",
        "description": "Multi-channel product launch campaign for Q1 2026",
        "budget_amount": 50000.00,
        "channels": ["email", "social", "paid_ads"],
        "ai_generated": False,
    },
    {
        "org_index": 0,
        "name": "Brand Awareness Sprint",
        "status": "draft",
        "objective": "brand_awareness",
        "description": "30-day brand awareness campaign across social channels",
        "budget_amount": 15000.00,
        "channels": ["social", "content_marketing"],
        "ai_generated": True,
    },
    {
        "org_index": 0,
        "name": "Email Nurture Sequence",
        "status": "active",
        "objective": "email_nurture",
        "description": "Automated email nurture flow for new signups",
        "budget_amount": 0.00,
        "channels": ["email"],
        "ai_generated": False,
    },
    {
        "org_index": 0,
        "name": "Holiday Retargeting",
        "status": "completed",
        "objective": "retargeting",
        "description": "Retargeting campaign for holiday shoppers",
        "budget_amount": 25000.00,
        "channels": ["paid_ads", "social"],
        "ai_generated": False,
    },
    {
        "org_index": 0,
        "name": "Content Syndication Push",
        "status": "paused",
        "objective": "lead_generation",
        "description": "Syndicate top-performing blog posts to generate leads",
        "budget_amount": 8000.00,
        "channels": ["content_marketing", "paid_ads"],
        "ai_generated": True,
    },
    # --- Acme Corp campaigns (org_index 1) ---
    {
        "org_index": 1,
        "name": "Spring Sale Blitz",
        "status": "active",
        "objective": "conversion",
        "description": "Flash sale promotion across all digital channels",
        "budget_amount": 30000.00,
        "channels": ["email", "social", "paid_ads"],
        "ai_generated": False,
    },
    {
        "org_index": 1,
        "name": "Thought Leadership Series",
        "status": "active",
        "objective": "brand_awareness",
        "description": "Weekly thought-leadership articles and social posts",
        "budget_amount": 5000.00,
        "channels": ["content_marketing", "social"],
        "ai_generated": True,
    },
    {
        "org_index": 1,
        "name": "Partner Referral Program",
        "status": "draft",
        "objective": "lead_generation",
        "description": "Partner-driven referral campaign with incentive tiers",
        "budget_amount": 20000.00,
        "channels": ["email", "content_marketing"],
        "ai_generated": False,
    },
    {
        "org_index": 1,
        "name": "Webinar Promotion",
        "status": "completed",
        "objective": "product_launch",
        "description": "Promote quarterly product webinar series",
        "budget_amount": 3500.00,
        "channels": ["email", "social"],
        "ai_generated": False,
    },
    {
        "org_index": 1,
        "name": "App Onboarding Flow",
        "status": "paused",
        "objective": "email_nurture",
        "description": "Automated onboarding drip for new app users",
        "budget_amount": 0.00,
        "channels": ["email", "in_app"],
        "ai_generated": True,
    },
]

CONTENT_DATA = [
    # (campaign_index | None, org_index, title, content_type, body, status, generated_by_ai)
    (0, 0, "Introducing Astra 2.0 — What's New", "blog_post",
     "We're thrilled to announce Astra 2.0, featuring a completely redesigned dashboard, "
     "AI-powered campaign suggestions, and real-time analytics. Here's everything you need to know...",
     "published", False),
    (5, 1, "Spring Sale: Up to 40% Off All Plans", "email",
     "Hi {{first_name}}, Spring is here and so are the savings! For a limited time, enjoy up to "
     "40% off all Acme Corp plans. Don't miss out — this offer ends March 31.",
     "published", False),
    (6, 1, "5 AI Trends Marketers Can't Ignore in 2026", "blog_post",
     "Artificial intelligence continues to reshape digital marketing. From predictive audience "
     "segmentation to generative ad creative, here are the top five trends shaping the industry...",
     "review", True),
    (1, 0, "Behind the Scenes: Building Our Brand Voice", "social_media",
     "Authenticity wins. 🎯 Here's how our team crafted a brand voice that resonates with "
     "over 100K followers. Thread 🧵 #BrandStrategy #MarketingTips",
     "draft", True),
    (3, 0, "Holiday Recap: Record-Breaking Results", "email",
     "Dear {{first_name}}, The numbers are in! Our holiday campaign exceeded every benchmark. "
     "Revenue up 47%, engagement up 62%, and new customer acquisition up 31%.",
     "published", False),
]

WORKFLOWS_DATA = [
    # (org_index, name, description, status, nodes, edges)
    (0, "Campaign Launch Pipeline",
     "Automated workflow for launching new campaigns with approval gates",
     "active",
     [
         {"id": "node-1", "type": "trigger", "label": "Campaign Created", "config": {"event": "campaign.created"}},
         {"id": "node-2", "type": "condition", "label": "Budget Check", "config": {"field": "budget_amount", "operator": "gt", "value": 10000}},
         {"id": "node-3", "type": "action", "label": "Request Approval", "config": {"assignee_role": "admin"}},
         {"id": "node-4", "type": "action", "label": "Activate Campaign", "config": {"status": "active"}},
     ],
     [
         {"source": "node-1", "target": "node-2"},
         {"source": "node-2", "target": "node-3", "label": "high budget"},
         {"source": "node-2", "target": "node-4", "label": "low budget"},
         {"source": "node-3", "target": "node-4"},
     ]),
    (1, "Content Approval Flow",
     "Routes content through review stages before publishing",
     "active",
     [
         {"id": "node-1", "type": "trigger", "label": "Content Submitted", "config": {"event": "content.submitted"}},
         {"id": "node-2", "type": "action", "label": "AI Quality Check", "config": {"service": "ai_review"}},
         {"id": "node-3", "type": "action", "label": "Editor Review", "config": {"assignee_role": "admin"}},
         {"id": "node-4", "type": "action", "label": "Publish", "config": {"status": "published"}},
     ],
     [
         {"source": "node-1", "target": "node-2"},
         {"source": "node-2", "target": "node-3"},
         {"source": "node-3", "target": "node-4"},
     ]),
    (1, "Weekly Reporting",
     "Generates and distributes weekly performance reports",
     "draft",
     [
         {"id": "node-1", "type": "trigger", "label": "Schedule", "config": {"cron": "0 9 * * 1"}},
         {"id": "node-2", "type": "action", "label": "Collect Metrics", "config": {"sources": ["campaigns", "content", "analytics"]}},
         {"id": "node-3", "type": "action", "label": "Generate Report", "config": {"format": "pdf"}},
         {"id": "node-4", "type": "action", "label": "Email Report", "config": {"recipients": "team"}},
     ],
     [
         {"source": "node-1", "target": "node-2"},
         {"source": "node-2", "target": "node-3"},
         {"source": "node-3", "target": "node-4"},
     ]),
]

NOTIFICATIONS_DATA = [
    # (user_index, org_index, type, title, body, resource_type, channel, is_read)
    (0, 0, "campaign.status_changed", "Campaign Activated",
     "Q1 Product Launch has been moved to active status.", "campaign", "in_app", False),
    (0, 0, "content.published", "Content Published",
     "Your blog post 'Introducing Astra 2.0' has been published successfully.", "content", "in_app", True),
    (0, 0, "workflow.completed", "Workflow Completed",
     "Campaign Launch Pipeline finished executing for Holiday Retargeting.", "workflow", "in_app", False),
    (1, 1, "team.member_joined", "New Team Member",
     "Mike Johnson has joined Acme Corp as an operator.", "team_member", "in_app", True),
    (1, 1, "campaign.status_changed", "Campaign Paused",
     "App Onboarding Flow has been paused by the system.", "campaign", "email", False),
    (1, 1, "content.review_requested", "Review Requested",
     "5 AI Trends Marketers Can't Ignore in 2026 is ready for editorial review.", "content", "in_app", False),
    (2, 1, "campaign.assigned", "Campaign Assigned",
     "You've been assigned to Spring Sale Blitz.", "campaign", "in_app", False),
    (2, 1, "content.comment", "New Comment",
     "Sarah Chen commented on 'Spring Sale: Up to 40% Off All Plans'.", "content", "in_app", True),
    (0, 0, "system.maintenance", "Scheduled Maintenance",
     "Platform maintenance is scheduled for Sunday 2 AM–4 AM UTC.", "system", "email", False),
    (2, 1, "workflow.failed", "Workflow Error",
     "Weekly Reporting failed: missing data source configuration.", "workflow", "in_app", False),
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


async def seed() -> None:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://astra:astra_dev@localhost:5432/astra",
    )
    engine, session_factory = create_session_factory(db_url)

    async with session_factory() as session:
        result = await session.execute(select(UserModel).limit(1))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        now = datetime.now(UTC)

        # --- Users --------------------------------------------------------
        pw_hash = hash_password(SEED_PASSWORD)
        users: list[UserModel] = []
        for user_data in USERS_DATA:
            user = UserModel(**user_data, password_hash=pw_hash)
            session.add(user)
            users.append(user)
        await session.flush()
        print(f"  Created {len(users)} users")

        # --- Organizations ------------------------------------------------
        orgs: list[OrganizationModel] = []
        for org_data in ORGANIZATIONS_DATA:
            org = OrganizationModel(**org_data)
            session.add(org)
            orgs.append(org)
        await session.flush()
        print(f"  Created {len(orgs)} organizations")

        # --- Team Members -------------------------------------------------
        team_members: list[TeamMemberModel] = []
        for user_idx, org_idx, role, permissions in TEAM_MEMBERS_DATA:
            member = TeamMemberModel(
                user_id=users[user_idx].id,
                organization_id=orgs[org_idx].id,
                role=role,
                permissions=permissions,
            )
            session.add(member)
            team_members.append(member)
        await session.flush()
        print(f"  Created {len(team_members)} team members")

        # --- Campaigns ---------------------------------------------------
        campaigns: list[CampaignModel] = []
        for i, camp_data in enumerate(CAMPAIGNS_DATA):
            org_idx = camp_data.pop("org_index")
            org_id = orgs[org_idx].id
            created_by = users[0 if org_idx == 0 else 1].id

            # Stagger dates so campaigns feel realistic
            start = now - timedelta(days=30 - i * 3)
            end = start + timedelta(days=60)

            campaign = CampaignModel(
                organization_id=org_id,
                start_date=start.date(),
                end_date=end.date(),
                created_by=created_by,
                **camp_data,
            )
            session.add(campaign)
            campaigns.append(campaign)
        await session.flush()
        print(f"  Created {len(campaigns)} campaigns")

        # --- Content Items -----------------------------------------------
        contents: list[ContentModel] = []
        for camp_idx, org_idx, title, content_type, body, status, gen_ai in CONTENT_DATA:
            campaign_id = campaigns[camp_idx].id if camp_idx is not None else None
            created_by = users[0 if org_idx == 0 else 1].id

            published_at = now - timedelta(days=5) if status == "published" else None
            scheduled_at = now + timedelta(days=7) if status == "draft" else None

            content = ContentModel(
                campaign_id=campaign_id,
                organization_id=orgs[org_idx].id,
                title=title,
                content_type=content_type,
                body=body,
                status=status,
                generated_by_ai=gen_ai,
                created_by=created_by,
                published_at=published_at,
                scheduled_at=scheduled_at,
            )
            session.add(content)
            contents.append(content)
        await session.flush()
        print(f"  Created {len(contents)} content items")

        # --- Workflows ---------------------------------------------------
        workflows: list[WorkflowModel] = []
        for org_idx, name, description, status, nodes, edges in WORKFLOWS_DATA:
            workflow = WorkflowModel(
                organization_id=orgs[org_idx].id,
                name=name,
                description=description,
                status=status,
                nodes=nodes,
                edges=edges,
                created_by=users[0 if org_idx == 0 else 1].id,
            )
            session.add(workflow)
            workflows.append(workflow)
        await session.flush()
        print(f"  Created {len(workflows)} workflows")

        # --- Notifications -----------------------------------------------
        notifications: list[NotificationModel] = []
        for user_idx, org_idx, ntype, title, body, resource_type, channel, is_read in NOTIFICATIONS_DATA:
            read_at = now if is_read else None

            notification = NotificationModel(
                organization_id=orgs[org_idx].id,
                user_id=users[user_idx].id,
                type=ntype,
                title=title,
                body=body,
                resource_type=resource_type,
                resource_id="",
                channel=channel,
                is_read=is_read,
                read_at=read_at,
            )
            session.add(notification)
            notifications.append(notification)
        await session.flush()
        print(f"  Created {len(notifications)} notifications")

        # --- Commit ------------------------------------------------------
        await session.commit()

        print()
        print("✓ Seed complete!")
        print(f"  Users:          {len(users)}")
        print(f"  Organizations:  {len(orgs)}")
        print(f"  Team Members:   {len(team_members)}")
        print(f"  Campaigns:      {len(campaigns)}")
        print(f"  Content Items:  {len(contents)}")
        print(f"  Workflows:      {len(workflows)}")
        print(f"  Notifications:  {len(notifications)}")
        print()
        print(f"  Login:    {SEED_EMAIL}")
        print(f"  Password: {SEED_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
