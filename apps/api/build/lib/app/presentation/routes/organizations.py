from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.organizations import (
    CreateOrganizationUseCase,
    GetOrganizationUseCase,
    ListUserOrganizationsUseCase,
    UpdateOrganizationUseCase,
)
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenError,
)
from app.presentation.dependencies import (
    get_create_org_use_case,
    get_db,
    get_get_org_use_case,
    get_list_orgs_use_case,
    get_update_org_use_case,
    pagination_params,
)
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import OrganizationResponse, PaginatedResponse

router = APIRouter()


class CreateOrganizationRequest(BaseModel):
    name: str
    slug: str


class UpdateOrganizationRequest(BaseModel):
    name: str | None = None
    settings: dict | None = None


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create organization")
async def create_organization(
    request: CreateOrganizationRequest,
    use_case: CreateOrganizationUseCase = Depends(get_create_org_use_case),
    user_id: UUID = Depends(require_user_id),
) -> OrganizationResponse:
    try:
        org = await use_case.execute(name=request.name, slug=request.slug, owner_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan_tier=org.plan_tier,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("/my", summary="List user organizations")
async def list_my_organizations(
    use_case: ListUserOrganizationsUseCase = Depends(get_list_orgs_use_case),
    user_id: UUID = Depends(require_user_id),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse[OrganizationResponse]:
    orgs = await use_case.execute(user_id=user_id)
    items = [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            plan_tier=org.plan_tier,
            settings=org.settings,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )
        for org in orgs
    ]
    total = len(items)
    page = pagination["page"]
    limit = pagination["limit"]
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    )


@router.get("/{org_id}", summary="Get organization details")
async def get_organization(
    org_id: UUID,
    use_case: GetOrganizationUseCase = Depends(get_get_org_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        org = await use_case.execute(org_id=org_id, user_id=user_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        ) from None
    except ForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied") from None
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan_tier=org.plan_tier,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.patch("/{org_id}", summary="Update organization")
async def update_organization(
    org_id: UUID,
    request: UpdateOrganizationRequest,
    use_case: UpdateOrganizationUseCase = Depends(get_update_org_use_case),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        org = await use_case.execute(
            org_id=org_id,
            user_id=user_id,
            name=request.name,
            settings=request.settings,
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        ) from None
    except ForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied") from None
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan_tier=org.plan_tier,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )
