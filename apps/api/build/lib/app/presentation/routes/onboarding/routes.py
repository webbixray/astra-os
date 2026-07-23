"""Self-Serve Onboarding API Routes — E6.3 Beta Launch.

Endpoints for public signup, organization creation, onboarding wizard,
and sample campaign/template provisioning.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.domain.common import now
from app.domain.entities.organization import Organization
from app.domain.entities.team_member import TeamMember
from app.domain.entities.organization import ORG_ROLES
from app.domain.entities.user import User
from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.infrastructure.auth.password import hash_password
from app.infrastructure.auth.jwt import JWTService
from app.presentation.dependencies import get_db
from app.presentation.dependencies import get_user_repo
from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl
from app.presentation.middleware.auth import require_user_id

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# --- Request/Response Models ---


class SignUpRequest(BaseModel):
    """Public signup request."""

    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    organization_name: str = Field(min_length=1, max_length=200)
    organization_slug: str | None = Field(None, pattern=r"^[a-z0-9-]+$", max_length=50)
    role: str = Field(default="marketer")
    company_size: str | None = Field(None, pattern=r"^(1-10|11-50|51-200|201-500|501-1000|1000+)$")
    use_case: str | None = Field(None, max_length=500)
    referral_code: str | None = None


class SignUpResponse(BaseModel):
    """Public signup response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]
    organization: dict[str, Any]
    onboarding_url: str


class OnboardingStepRequest(BaseModel):
    """Generic onboarding step completion."""

    step: str
    data: dict[str, Any] = {}
    skip: bool = False


class OnboardingStateResponse(BaseModel):
    """Current onboarding state for user."""

    current_step: str
    completed_steps: list[str]
    total_steps: int
    organization: dict[str, Any] | None = None
    sample_data_provisioned: bool = False


class ProvisionSampleDataRequest(BaseModel):
    """Request to provision sample campaigns/templates."""

    campaign_types: list[str] = Field(default_factory=lambda: ["social", "search", "email"])
    include_templates: bool = True
    include_brand_voice: bool = True
    ad_accounts: list[str] | None = None


class SampleDataResponse(BaseModel):
    """Response after sample data provisioning."""

    campaigns_created: int
    templates_created: int
    brand_voices_created: int
    workflows_created: int


# --- Helper Functions ---


def _generate_org_slug(name: str) -> str:
    """Generate a URL-safe slug from organization name."""
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    slug = slug.strip("-")
    if len(slug) > 50:
        slug = slug[:50].rstrip("-")
    return slug or "org"


def _get_onboarding_steps() -> list[dict[str, Any]]:
    """Define the onboarding wizard steps."""
    return [
        {"id": "welcome", "title": "Welcome", "description": "Get to know ASTRA OS", "order": 1},
        {"id": "brand", "title": "Brand Setup", "description": "Add your brand voice, colors, and guidelines", "order": 2},
        {"id": "channels", "title": "Connect Channels", "description": "Link your ad accounts and social profiles", "order": 3},
        {"id": "team", "title": "Invite Team", "description": "Add colleagues to collaborate", "order": 4},
        {"id": "first_campaign", "title": "Launch Campaign", "description": "Create your first AI-assisted campaign", "order": 5},
        {"id": "sample_data", "title": "Try Sample Data", "description": "Explore with pre-built campaigns and templates", "order": 6},
    ]


async def _get_user_onboarding_state(user_id: UUID, db: AsyncSession) -> dict[str, Any]:
    """Get or create onboarding state for user."""
    # In production, this would be stored in a dedicated onboarding_state table
    # For now, we'll derive from user/organization state
    from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
    from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl

    user_repo = UserRepositoryImpl(db)
    org_repo = OrganizationRepositoryImpl(db)
    team_repo = TeamMemberRepositoryImpl(db)

    user = await user_repo.find_by_id(user_id)
    if not user:
        return {"current_step": "welcome", "completed_steps": [], "sample_data_provisioned": False}

    # Get user's organizations
    team_memberships = await team_repo.find_by_user(user_id)
    org_ids = [tm.organization_id for tm in team_memberships]

    organizations = []
    for org_id in org_ids:
        org = await org_repo.find_by_id(org_id)
        if org:
            organizations.append(org.to_dict())

    # Determine current step based on organization state
    completed_steps = []
    current_step = "welcome"

    if organizations:
        org = organizations[0]
        completed_steps.append("welcome")
        current_step = "brand"

        # Check if brand voice exists
        if org.get("brand_voice_id"):
            completed_steps.append("brand")
            current_step = "channels"

        # Check if ad accounts connected
        if org.get("ad_accounts_connected", 0) > 0:
            completed_steps.append("channels")
            current_step = "team"

        # Check team members
        if len(org.get("team_members", [])) > 1:
            completed_steps.append("team")
            current_step = "first_campaign"

        # Check campaigns
        if org.get("campaigns_created", 0) > 0:
            completed_steps.append("first_campaign")
            current_step = "sample_data"

    return {
        "current_step": current_step,
        "completed_steps": completed_steps,
        "total_steps": len(_get_onboarding_steps()),
        "organizations": organizations,
        "sample_data_provisioned": False,  # Would track in DB
    }


async def _create_organization_with_owner(
    db: AsyncSession,
    name: str,
    slug: str,
    owner_id: UUID,
) -> Organization:
    """Create organization and add owner as team member."""
    org = Organization.create(name=name, slug=slug)
    db.add(org)
    await db.flush()

    # Add owner as team member
    team_member = TeamMember.create(
        organization_id=org.id,
        user_id=owner_id,
        role="owner",
    )
    db.add(team_member)
    await db.flush()

    return org


async def _provision_sample_data(
    db: AsyncSession,
    organization_id: UUID,
    user_id: UUID,
    campaign_types: list[str],
    include_templates: bool,
    include_brand_voice: bool,
) -> dict[str, int]:
    """Provision sample campaigns, templates, and brand voices for new org."""
    from app.domain.entities.campaigns import Campaign, CampaignStatus, CampaignObjective
    from app.domain.entities.content import ContentTemplate, ContentType
    from app.domain.entities.brand_voice import BrandVoice
    from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
    from app.infrastructure.db.repositories.content_template_repository import ContentTemplateRepositoryImpl
    from app.infrastructure.db.repositories.brand_voice_repository import BrandVoiceRepositoryImpl

    campaign_repo = CampaignRepositoryImpl(db)
    template_repo = ContentTemplateRepositoryImpl(db)
    brand_voice_repo = BrandVoiceRepositoryImpl(db)

    results = {
        "campaigns_created": 0,
        "templates_created": 0,
        "brand_voices_created": 0,
        "workflows_created": 0,
    }

    # Create sample brand voice
    if include_brand_voice:
        brand_voice = BrandVoice.create(
            organization_id=organization_id,
            name="Default Brand Voice",
            description="Professional, confident, and approachable brand voice",
            tone_attributes={
                "professional": 0.8,
                "friendly": 0.7,
                "authoritative": 0.6,
                "innovative": 0.5,
            },
            vocabulary_preferences={
                "preferred": ["innovative", "solution", "transform", "empower", "seamless"],
                "avoid": ["cheap", "basic", "simple", "just"],
            },
            style_guide="Use active voice. Keep sentences concise. Focus on customer value.",
            example_content="Transform your marketing with AI-powered campaigns that drive real results.",
            created_by=user_id,
        )
        await brand_voice_repo.save(brand_voice)
        results["brand_voices_created"] = 1

    # Create sample content templates
    if include_templates:
        templates = [
            ContentTemplate.create(
                organization_id=organization_id,
                name="Social Media Announcement",
                description="Template for product/feature announcements on social media",
                content_type=ContentType.SOCIAL_POST,
                template_text="""
🚀 Exciting news! {product_name} now {key_benefit}.

{value_proposition}

✨ {feature_1}
✨ {feature_2}
✨ {feature_3}

{call_to_action}

#{hashtag_1} #{hashtag_2} #{brand_hashtag}
""".strip(),
                variables=[
                    "product_name",
                    "key_benefit",
                    "value_proposition",
                    "feature_1",
                    "feature_2",
                    "feature_3",
                    "call_to_action",
                    "hashtag_1",
                    "hashtag_2",
                    "brand_hashtag",
                ],
                platform="linkedin",
                created_by=user_id,
            ),
            ContentTemplate.create(
                organization_id=organization_id,
                name="Email Newsletter",
                description="Weekly newsletter template for customer updates",
                content_type=ContentType.EMAIL,
                template_text="""
Subject: {subject_line}

Hi {first_name},

{opening_hook}

{main_content}

{cta_text}: {cta_link}

Best regards,
The {brand_name} Team

P.S. {postscript}
""".strip(),
                variables=[
                    "subject_line",
                    "first_name",
                    "opening_hook",
                    "main_content",
                    "cta_text",
                    "cta_link",
                    "brand_name",
                    "postscript",
                ],
                platform="email",
                created_by=user_id,
            ),
            ContentTemplate.create(
                organization_id=organization_id,
                name="Blog Post - How-To Guide",
                description="Educational blog post template for SEO",
                content_type=ContentType.BLOG_POST,
                template_text="""
# {title}

## Introduction
{introduction}

## What You'll Learn
{learning_objectives}

## Step 1: {step_1_title}
{step_1_content}

## Step 2: {step_2_title}
{step_2_content}

## Step 3: {step_3_title}
{step_3_content}

## Conclusion
{conclusion}

## Next Steps
{next_steps}
""".strip(),
                variables=[
                    "title",
                    "introduction",
                    "learning_objectives",
                    "step_1_title",
                    "step_1_content",
                    "step_2_title",
                    "step_2_content",
                    "step_3_title",
                    "step_3_content",
                    "conclusion",
                    "next_steps",
                ],
                platform="blog",
                created_by=user_id,
            ),
        ]
        for template in templates:
            await template_repo.save(template)
        results["templates_created"] = len(templates)

    # Create sample campaigns
    if campaign_types:
        sample_campaigns = []

        if "social" in campaign_types:
            sample_campaigns.append(
                Campaign.create(
                    organization_id=organization_id,
                    name="Sample: Social Media Launch",
                    description="Launch campaign for new product on social platforms",
                    objective=CampaignObjective.BRAND_AWARENESS,
                    status=CampaignStatus.DRAFT,
                    budget_cents=500000,  # $5,000
                    daily_budget_cents=50000,
                    start_date=now(),
                    end_date=None,
                    target_audience={
                        "age_range": "25-45",
                        "interests": ["technology", "marketing", "AI"],
                        "locations": ["US", "CA", "UK"],
                    },
                    platforms=["meta", "linkedin"],
                    created_by=user_id,
                )
            )

        if "search" in campaign_types:
            sample_campaigns.append(
                Campaign.create(
                    organization_id=organization_id,
                    name="Sample: Search Campaign",
                    description="High-intent search campaign for lead generation",
                    objective=CampaignObjective.LEAD_GENERATION,
                    status=CampaignStatus.DRAFT,
                    budget_cents=1000000,  # $10,000
                    daily_budget_cents=100000,
                    start_date=now(),
                    end_date=None,
                    target_audience={
                        "keywords": ["AI marketing", "campaign automation", "marketing OS"],
                        "match_types": ["exact", "phrase"],
                        "negative_keywords": ["free", "cheap", "trial"],
                    },
                    platforms=["google"],
                    created_by=user_id,
                )
            )

        if "email" in campaign_types:
            sample_campaigns.append(
                Campaign.create(
                    organization_id=organization_id,
                    name="Sample: Email Nurture Sequence",
                    description="5-email nurture sequence for new leads",
                    objective=CampaignObjective.CONVERSION,
                    status=CampaignStatus.DRAFT,
                    budget_cents=100000,  # $1,000
                    daily_budget_cents=10000,
                    start_date=now(),
                    end_date=None,
                    target_audience={
                        "segments": ["new_subscribers", "trial_users"],
                        "frequency": "every_3_days",
                    },
                    platforms=["email"],
                    created_by=user_id,
                )
            )

        for campaign in sample_campaigns:
            await campaign_repo.save(campaign)
        results["campaigns_created"] = len(sample_campaigns)

    await db.commit()
    return results


# --- Routes ---


@router.post(
    "/signup",
    response_model=SignUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public self-serve signup",
)
async def signup(
    request: SignUpRequest,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepositoryImpl = Depends(get_user_repo),
) -> SignUpResponse:
    """Create new user, organization, and start onboarding."""
    # Check if user already exists
    existing = await user_repo.find_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate password strength
    from app.application.use_cases.auth_use_cases import validate_password_strength

    validate_password_strength(request.password)

    # Generate organization slug
    org_slug = request.organization_slug or _generate_org_slug(request.organization_name)

    # Check slug uniqueness
    from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl

    org_repo = OrganizationRepositoryImpl(db)
    existing_org = await org_repo.find_by_slug(org_slug)
    if existing_org:
        org_slug = f"{org_slug}-{uuid4().hex[:6]}"

    # Create user
    password_hash = hash_password(request.password)
    user = User.create(
        email=request.email,
        name=request.name,
        password_hash=password_hash,
    )
    db.add(user)
    await db.flush()

    # Create organization with owner
    org = await _create_organization_with_owner(db, request.organization_name, org_slug, user.id)

    # Create JWT tokens
    jwt_service = JWTService()
    access_token = jwt_service.create_access_token(str(user.id))
    refresh_token = jwt_service.create_refresh_token(str(user.id))

    # Publish domain event
    await EventBus.publish(
        DomainEvent.create(
            event_type=DomainEventType.USER_SIGNED_UP,
            aggregate_id=str(user.id),
            aggregate_type="user",
            data={
                "email": user.email,
                "name": user.name,
                "organization_id": str(org.id),
                "organization_name": org.name,
                "signup_source": "self_serve",
                "company_size": request.company_size,
                "use_case": request.use_case,
                "referral_code": request.referral_code,
            },
        )
    )

    await EventBus.publish(
        DomainEvent.create(
            event_type=DomainEventType.ORGANIZATION_CREATED,
            aggregate_id=str(org.id),
            aggregate_type="organization",
            data={
                "name": org.name,
                "slug": org.slug,
                "owner_id": str(user.id),
                "signup_source": "self_serve",
            },
        )
    )

    await db.commit()

    return SignUpResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        organization={
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "created_at": org.created_at.isoformat(),
        },
        onboarding_url=f"/onboarding/wizard?org={org.id}",
    )


@router.get(
    "/wizard/state",
    response_model=OnboardingStateResponse,
    summary="Get current onboarding state",
)
async def get_onboarding_state(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OnboardingStateResponse:
    """Get the current onboarding wizard state for the authenticated user."""
    from app.presentation.middleware.auth import require_user_id
    from app.presentation.dependencies import get_user_id

    # Get user ID from auth middleware
    try:
        user_id = await get_user_id(request)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")

    state = await _get_user_onboarding_state(user_id, db)

    return OnboardingStateResponse(
        current_step=state["current_step"],
        completed_steps=state["completed_steps"],
        total_steps=state["total_steps"],
        organization=state["organizations"][0] if state["organizations"] else None,
        sample_data_provisioned=state["sample_data_provisioned"],
    )


@router.get(
    "/wizard/steps",
    response_model=list[dict[str, Any]],
    summary="Get all onboarding steps",
)
async def get_onboarding_steps() -> list[dict[str, Any]]:
    """Get the complete onboarding wizard step definitions."""
    return _get_onboarding_steps()


@router.post(
    "/wizard/step",
    response_model=dict,
    summary="Complete an onboarding step",
)
async def complete_onboarding_step(
    request: OnboardingStepRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    """Mark an onboarding step as completed."""
    # In production, persist to onboarding_state table
    # For now, return success
    steps = _get_onboarding_steps()
    step_ids = [s["id"] for s in steps]

    if request.step not in step_ids:
        raise HTTPException(status_code=400, detail=f"Invalid step: {request.step}")

    return {
        "step": request.step,
        "completed": True,
        "data": request.data,
        "next_step": steps[step_ids.index(request.step) + 1]["id"]
        if step_ids.index(request.step) + 1 < len(steps)
        else None,
    }


@router.post(
    "/provision-sample-data",
    response_model=SampleDataResponse,
    summary="Provision sample campaigns, templates, and brand voices",
)
async def provision_sample_data(
    request: ProvisionSampleDataRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_user_id),
) -> SampleDataResponse:
    """Provision sample data for a new organization to explore the platform."""
    from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl

    team_repo = TeamMemberRepositoryImpl(db)
    memberships = await team_repo.find_by_user(user_id)

    if not memberships:
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    organization_id = memberships[0].organization_id

    results = await _provision_sample_data(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        campaign_types=request.campaign_types,
        include_templates=request.include_templates,
        include_brand_voice=request.include_brand_voice,
    )

    return SampleDataResponse(**results)


@router.get(
    "/check-slug/{slug}",
    response_model=dict,
    summary="Check organization slug availability",
)
async def check_slug_availability(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if an organization slug is available."""
    from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl

    org_repo = OrganizationRepositoryImpl(db)
    existing = await org_repo.find_by_slug(slug)

    return {"available": existing is None, "slug": slug}


@router.get(
    "/health",
    response_model=dict,
    summary="Onboarding service health check",
)
async def onboarding_health() -> dict:
    """Health check for onboarding service."""
    return {
        "status": "healthy",
        "service": "onboarding",
        "version": "1.0.0",
        "features": {
            "self_serve_signup": True,
            "onboarding_wizard": True,
            "sample_data_provisioning": True,
            "slug_availability_check": True,
        },
    }