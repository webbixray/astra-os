from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.feature_flag_repository import FeatureFlagRepository
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.presentation.dependencies import get_db

if TYPE_CHECKING:
    from uuid import UUID


async def get_organization_plan_tier(organization_id: UUID, db: AsyncSession) -> str:
    """Get the organization's current plan tier."""
    org_repo = OrganizationRepositoryImpl(db)
    org = await org_repo.find_by_id(organization_id)
    return org.plan_tier if org else "free"


FEATURE_PRESETS: dict[str, list[str]] = {
    "free": ["basic_analytics", "content_management"],
    "starter": ["basic_analytics", "content_management", "email_marketing", "campaign_management"],
    "professional": [
        "advanced_analytics",
        "content_management",
        "email_marketing",
        "campaign_management",
        "custom_reports",
        "workflow_automation",
        "ab_testing",
        "advertising_integration",
    ],
    "business": [
        "advanced_analytics",
        "content_management",
        "email_marketing",
        "campaign_management",
        "custom_reports",
        "workflow_automation",
        "ab_testing",
        "advertising_integration",
        "ai_content_generation",
        "multi_platform_publishing",
        "advanced_workflows",
        "api_access",
    ],
    "enterprise": [
        "advanced_analytics",
        "content_management",
        "email_marketing",
        "campaign_management",
        "custom_reports",
        "workflow_automation",
        "ab_testing",
        "advertising_integration",
        "ai_content_generation",
        "multi_platform_publishing",
        "advanced_workflows",
        "api_access",
        "white_label",
        "saml_sso",
        "dedicated_infrastructure",
        "audit_logs",
    ],
}


def get_plan_features(plan_tier: str) -> set[str]:
    return set(FEATURE_PRESETS.get(plan_tier, FEATURE_PRESETS["free"]))


async def require_feature(
    feature_key: str,
    organization_id: UUID,
    plan_tier: str = "auto",
    db: AsyncSession = Depends(get_db),
) -> bool:
    # Auto-fetch plan tier from organization if "auto" is specified
    if plan_tier == "auto":
        plan_tier = await get_organization_plan_tier(organization_id, db)
    repo = FeatureFlagRepository(db)

    plan_features = get_plan_features(plan_tier)
    if feature_key in plan_features:
        return True

    override = await repo.find_by_key(organization_id, feature_key)
    if override and override.is_enabled:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "feature_not_available",
            "message": f"The feature '{feature_key}' is not available on your current plan. "
            f"Please upgrade to access this feature.",
            "feature": feature_key,
            "current_plan": plan_tier,
        },
    )


class FeatureGate:
    def __init__(self, feature_key: str):
        self.feature_key = feature_key

    async def __call__(
        self,
        organization_id: UUID,
        plan_tier: str = "auto",
        db: AsyncSession = Depends(get_db),
    ) -> None:
        await require_feature(self.feature_key, organization_id, plan_tier, db)


AD_FEATURES = FeatureGate("advertising_integration")
AI_CONTENT_FEATURE = FeatureGate("ai_content_generation")
WORKFLOW_FEATURE = FeatureGate("workflow_automation")
AB_TEST_FEATURE = FeatureGate("ab_testing")
EMAIL_FEATURE = FeatureGate("email_marketing")
ADVANCED_REPORTS_FEATURE = FeatureGate("custom_reports")
PUBLISHING_FEATURE = FeatureGate("multi_platform_publishing")
