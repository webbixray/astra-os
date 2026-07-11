from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.advertising.ad_account_service import AdAccountService
from app.application.use_cases.advertising.ad_campaign_service import AdCampaignService
from app.application.use_cases.advertising.ad_creative_service import AdCreativeService
from app.infrastructure.db.repositories.advertising.advertising_repository import (
    AdAccountRepository,
    AdCampaignRepository,
    AdCreativeRepository,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.feature_flags import require_feature
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


# --- Schemas ---

class ConnectAccountRequest(BaseModel):
    organization_id: UUID
    platform: str
    account_name: str
    platform_account_id: str
    credentials: dict = {}


class CreateCampaignRequest(BaseModel):
    organization_id: UUID
    ad_account_id: UUID
    name: str
    objective: str = "awareness"


class CreateCreativeRequest(BaseModel):
    organization_id: UUID
    name: str
    type: str = "image"
    ad_campaign_id: UUID | None = None


class UpdateCreativeRequest(BaseModel):
    headline: str | None = None
    body: str | None = None
    destination_url: str | None = None
    status: str | None = None


# --- Dependencies ---

def get_account_service(db: AsyncSession = Depends(get_db)) -> AdAccountService:
    return AdAccountService(AdAccountRepository(db))


def get_campaign_service(db: AsyncSession = Depends(get_db)) -> AdCampaignService:
    return AdCampaignService(AdCampaignRepository(db))


def get_creative_service(db: AsyncSession = Depends(get_db)) -> AdCreativeService:
    return AdCreativeService(AdCreativeRepository(db))


# --- Ad Account Routes ---

@router.post("/ad/accounts", status_code=201)
async def connect_account(
    request: ConnectAccountRequest,
    service: AdAccountService = Depends(get_account_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("advertising_integration", request.organization_id, "auto", db)
    return await service.connect(
        organization_id=request.organization_id,
        platform=request.platform,
        account_name=request.account_name,
        platform_account_id=request.platform_account_id,
        credentials=request.credentials,
    )


@router.get("/ad/accounts")
async def list_accounts(
    organization_id: UUID,
    service: AdAccountService = Depends(get_account_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", organization_id, "auto", db)
    return await service.list_accounts(organization_id)


@router.post("/ad/accounts/{account_id}/disconnect")
async def disconnect_account(
    account_id: UUID,
    service: AdAccountService = Depends(get_account_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    account = await service.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found") from None
    await require_org_role(account.organization_id, "admin", user_id, db)
    await require_feature("advertising_integration", account.organization_id, "auto", db)
    return await service.disconnect(account_id)


@router.post("/ad/accounts/{account_id}/sync")
async def sync_account(
    account_id: UUID,
    service: AdAccountService = Depends(get_account_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    account = await service.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found") from None
    await require_org_role(account.organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", account.organization_id, "auto", db)
    return await service.sync(account_id)


# --- Ad Campaign Routes ---

@router.post("/ad/campaigns", status_code=201)
async def create_ad_campaign(
    request: CreateCampaignRequest,
    service: AdCampaignService = Depends(get_campaign_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("advertising_integration", request.organization_id, "auto", db)
    return await service.create(
        organization_id=request.organization_id,
        ad_account_id=request.ad_account_id,
        name=request.name,
        objective=request.objective,
    )


@router.get("/ad/campaigns")
async def list_ad_campaigns(
    organization_id: UUID,
    service: AdCampaignService = Depends(get_campaign_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", organization_id, "auto", db)
    return await service.list_by_organization(organization_id)


@router.post("/ad/campaigns/{campaign_id}/sync")
async def sync_campaign(
    campaign_id: UUID,
    service: AdCampaignService = Depends(get_campaign_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    campaign = await service.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found") from None
    await require_org_role(campaign.organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", campaign.organization_id, "auto", db)
    return await service.sync_to_platform(campaign_id)


# --- Ad Creative Routes ---

@router.post("/ad/creatives", status_code=201)
async def create_creative(
    request: CreateCreativeRequest,
    service: AdCreativeService = Depends(get_creative_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(request.organization_id, "member", user_id, db)
    await require_feature("advertising_integration", request.organization_id, "auto", db)
    return await service.create(
        organization_id=request.organization_id,
        name=request.name,
        type=request.type,
        ad_campaign_id=request.ad_campaign_id,
    )


@router.get("/ad/creatives")
async def list_creatives(
    organization_id: UUID,
    service: AdCreativeService = Depends(get_creative_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", organization_id, "auto", db)
    return await service.list_by_organization(organization_id)


@router.patch("/ad/creatives/{creative_id}")
async def update_creative(
    creative_id: UUID,
    request: UpdateCreativeRequest,
    service: AdCreativeService = Depends(get_creative_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    creative = await service.get_by_id(creative_id)
    if not creative:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creative not found") from None
    await require_org_role(creative.organization_id, "viewer", user_id, db)
    await require_feature("advertising_integration", creative.organization_id, "auto", db)
    return await service.update(
        creative_id=creative_id,
        headline=request.headline,
        body=request.body,
        destination_url=request.destination_url,
        status=request.status,
    )
