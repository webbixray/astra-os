"""Creative Management API — CRUD, approval workflow, campaign association.

Endpoints:
    POST   /creatives                  — Create creative
    GET    /creatives                  — List creatives (org-wide)
    GET    /creatives/{id}             — Get creative detail
    PUT    /creatives/{id}             — Update creative
    DELETE /creatives/{id}             — Delete creative
    POST   /creatives/{id}/submit     — Submit for review
    POST   /creatives/{id}/approve    — Approve
    POST   /creatives/{id}/reject     — Reject
    POST   /creatives/{id}/associate/{campaign_id} — Associate to campaign
    GET    /creatives/campaign/{campaign_id}         — List by campaign
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.campaigns.creative_use_cases import (
    ApproveCreativeUseCase,
    AssociateCreativeToCampaignUseCase,
    CreateCreativeUseCase,
    DeleteCreativeUseCase,
    GetCreativeUseCase,
    ListCreativesByCampaignUseCase,
    ListCreativesUseCase,
    RejectCreativeUseCase,
    SubmitCreativeForReviewUseCase,
    UpdateCreativeUseCase,
)
from app.domain.entities.advertising.ad_creative import CreativeType
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.infrastructure.db.repositories.campaigns.creative_repository import (
    CreativeRepositoryImpl,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


# ── Request schemas ──────────────────────────────────────────────────


class CreateCreativeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="image", description="image|video|carousel|text|html")
    headline: str = ""
    body: str = ""
    destination_url: str = ""
    asset_urls: list[str] = []


class UpdateCreativeRequest(BaseModel):
    name: str | None = None
    headline: str | None = None
    body: str | None = None
    destination_url: str | None = None
    asset_urls: list[str] | None = None


class RejectCreativeRequest(BaseModel):
    reason: str = ""


# ── Dependency injection ─────────────────────────────────────────────


async def get_creative_repo(db: AsyncSession = Depends(get_db)) -> CreativeRepositoryImpl:
    return CreativeRepositoryImpl(db)


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a creative asset")
async def create_creative(
    request: CreateCreativeRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        # Resolve org from user (simplified — real impl uses tenant middleware)
        from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found") from None
        org_id = user.organization_id

        await require_org_role(org_id, "member", user_id, db)

        repo = CreativeRepositoryImpl(db)
        use_case = CreateCreativeUseCase(repo)
        creative = await use_case.execute(
            organization_id=org_id,
            name=request.name,
            created_by=user_id,
            type=CreativeType(request.type),
            headline=request.headline,
            body=request.body,
            destination_url=request.destination_url,
            asset_urls=request.asset_urls,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None

    return {
        "id": str(creative.id),
        "name": creative.name,
        "type": creative.type.value,
        "status": creative.status.value,
        "headline": creative.headline,
        "body": creative.body,
        "destination_url": creative.destination_url,
        "asset_urls": creative.asset_urls,
        "created_at": creative.created_at.isoformat(),
    }


@router.get("/", summary="List creatives for organization")
async def list_creatives(
    status_filter: str | None = None,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

    user_repo = UserRepositoryImpl(db)
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found") from None
    org_id = user.organization_id

    await require_org_role(org_id, "viewer", user_id, db)

    from app.domain.entities.advertising.ad_creative import CreativeStatus

    cs = CreativeStatus(status_filter) if status_filter else None
    repo = CreativeRepositoryImpl(db)
    use_case = ListCreativesUseCase(repo)
    creatives = await use_case.execute(org_id, status=cs)

    return {
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "type": c.type.value,
                "status": c.status.value,
                "headline": c.headline,
                "campaign_id": str(c.ad_campaign_id) if c.ad_campaign_id else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in creatives
        ],
        "count": len(creatives),
    }


@router.get("/{creative_id}", summary="Get creative detail")
async def get_creative(
    creative_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = GetCreativeUseCase(repo)
        creative = await use_case.execute(creative_id)

        from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl

        user_repo = UserRepositoryImpl(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found") from None
        await require_org_role(creative.organization_id, "viewer", user_id, db)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None

    return {
        "id": str(creative.id),
        "name": creative.name,
        "type": creative.type.value,
        "status": creative.status.value,
        "headline": creative.headline,
        "body": creative.body,
        "destination_url": creative.destination_url,
        "asset_urls": creative.asset_urls,
        "campaign_id": str(creative.ad_campaign_id) if creative.ad_campaign_id else None,
        "created_at": creative.created_at.isoformat(),
        "updated_at": creative.updated_at.isoformat(),
    }


@router.put("/{creative_id}", summary="Update creative")
async def update_creative(
    creative_id: UUID,
    request: UpdateCreativeRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = UpdateCreativeUseCase(repo)
        creative = await use_case.execute(
            creative_id=creative_id,
            name=request.name,
            headline=request.headline,
            body=request.body,
            destination_url=request.destination_url,
            asset_urls=request.asset_urls,
        )
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, EntityNotFoundError) else 422,
            detail=str(e),
        ) from None

    return {
        "id": str(creative.id),
        "name": creative.name,
        "type": creative.type.value,
        "status": creative.status.value,
        "updated_at": creative.updated_at.isoformat(),
    }


@router.delete("/{creative_id}", status_code=204, summary="Delete creative")
async def delete_creative(
    creative_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = DeleteCreativeUseCase(repo)
        await use_case.execute(creative_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, EntityNotFoundError) else 422,
            detail=str(e),
        ) from None


@router.post("/{creative_id}/submit", summary="Submit creative for review")
async def submit_for_review(
    creative_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = SubmitCreativeForReviewUseCase(repo)
        creative = await use_case.execute(creative_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, EntityNotFoundError) else 422,
            detail=str(e),
        ) from None

    return {"id": str(creative.id), "status": creative.status.value}


@router.post("/{creative_id}/approve", summary="Approve creative")
async def approve_creative(
    creative_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = ApproveCreativeUseCase(repo)
        creative = await use_case.execute(creative_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, EntityNotFoundError) else 422,
            detail=str(e),
        ) from None

    return {"id": str(creative.id), "status": creative.status.value}


@router.post("/{creative_id}/reject", summary="Reject creative")
async def reject_creative(
    creative_id: UUID,
    request: RejectCreativeRequest = RejectCreativeRequest(),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = RejectCreativeUseCase(repo)
        creative = await use_case.execute(creative_id, reason=request.reason)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, EntityNotFoundError) else 422,
            detail=str(e),
        ) from None

    return {"id": str(creative.id), "status": creative.status.value}


@router.post(
    "/{creative_id}/associate/{campaign_id}",
    summary="Associate creative with campaign",
)
async def associate_to_campaign(
    creative_id: UUID,
    campaign_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        repo = CreativeRepositoryImpl(db)
        use_case = AssociateCreativeToCampaignUseCase(repo)
        creative = await use_case.execute(creative_id, campaign_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None

    return {
        "id": str(creative.id),
        "campaign_id": str(creative.ad_campaign_id),
    }


@router.get("/campaign/{campaign_id}", summary="List creatives for a campaign")
async def list_creatives_by_campaign(
    campaign_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = CreativeRepositoryImpl(db)
    use_case = ListCreativesByCampaignUseCase(repo)
    creatives = await use_case.execute(campaign_id)

    return {
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "type": c.type.value,
                "status": c.status.value,
                "headline": c.headline,
                "created_at": c.created_at.isoformat(),
            }
            for c in creatives
        ],
        "count": len(creatives),
    }
