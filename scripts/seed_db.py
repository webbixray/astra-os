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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.infrastructure.auth.password import hash_password
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.organization import OrganizationModel
from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.session import create_session_factory

SEED_EMAIL = "admin@astra.dev"
SEED_PASSWORD = "AstraAdmin1!"


SEED_USER = {
    "email": SEED_EMAIL,
    "name": "Astra Admin",
    "is_active": True,
}

SEED_ORG = {
    "name": "Astra Demo Organization",
    "slug": "astra-demo",
    "plan_tier": "professional",
}

SEED_CAMPAIGNS = [
    {
        "name": "Q1 Product Launch",
        "status": "active",
        "objective": "product_launch",
        "description": "Multi-channel product launch campaign for Q1 2026",
        "budget_amount": 50000.00,
    },
    {
        "name": "Brand Awareness Sprint",
        "status": "draft",
        "objective": "brand_awareness",
        "description": "30-day brand awareness campaign across social channels",
        "budget_amount": 15000.00,
    },
    {
        "name": "Email Nurture Sequence",
        "status": "active",
        "objective": "email_nurture",
        "description": "Automated email nurture flow for new signups",
        "budget_amount": 0.00,
    },
]


async def seed() -> None:
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://astra:astra_dev@localhost:5432/astra")
    engine, session_factory = create_session_factory(db_url)

    async with session_factory() as session:
        result = await session.execute(select(UserModel).limit(1))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        pw_hash = hash_password(SEED_PASSWORD)
        user = UserModel(**SEED_USER, password_hash=pw_hash)
        session.add(user)
        await session.flush()

        org = OrganizationModel(**SEED_ORG)
        session.add(org)
        await session.flush()

        membership = TeamMemberModel(
            user_id=user.id,
            organization_id=org.id,
            role="owner",
            permissions=[],
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
        print(f"Login:    {SEED_EMAIL}")
        print(f"Password: {SEED_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
