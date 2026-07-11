"""
Database seed script for development environment.

Usage:
    cd apps/api
    python -m scripts.seed_db

This script creates sample data for development and testing.
It is safe to run multiple times - it will skip existing data.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.organization import OrganizationModel
from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from sqlalchemy import select


SEED_USER = {
    "email": "admin@astra.dev",
    "full_name": "Astra Admin",
    "role": "owner",
    "is_active": True,
}

SEED_ORG = {
    "name": "Astra Demo Organization",
    "slug": "astra-demo",
    "plan": "professional",
    "is_active": True,
}

SEED_CAMPAIGNS = [
    {
        "name": "Q1 Product Launch",
        "status": "active",
        "type": "product_launch",
        "description": "Multi-channel product launch campaign for Q1 2026",
        "budget": 50000.00,
    },
    {
        "name": "Brand Awareness Sprint",
        "status": "draft",
        "type": "brand_awareness",
        "description": "30-day brand awareness campaign across social channels",
        "budget": 15000.00,
    },
    {
        "name": "Email Nurture Sequence",
        "status": "active",
        "type": "email_nurture",
        "description": "Automated email nurture flow for new signups",
        "budget": 0.00,
    },
]


async def seed() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).limit(1))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        user = UserModel(**SEED_USER)
        session.add(user)
        await session.flush()

        org = OrganizationModel(**SEED_ORG, owner_id=user.id)
        session.add(org)
        await session.flush()

        membership = TeamMemberModel(
            user_id=user.id,
            organization_id=org.id,
            role="owner",
            is_active=True,
        )
        session.add(membership)

        for campaign_data in SEED_CAMPAIGNS:
            campaign = CampaignModel(
                **campaign_data,
                organization_id=org.id,
                created_by=user.id,
            )
            session.add(campaign)

        await session.commit()
        print(f"Seeded: 1 user, 1 organization, {len(SEED_CAMPAIGNS)} campaigns")
        print(f"Login: {SEED_USER['email']}")


if __name__ == "__main__":
    asyncio.run(seed())
