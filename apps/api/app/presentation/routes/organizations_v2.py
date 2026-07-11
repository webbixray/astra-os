from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.organizations.org_service import OrganizationService
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenError,
    ValidationError,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter()


class CreateSubOrgRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class SetParentRequest(BaseModel):
    parent_org_id: UUID


class InviteMemberRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class ChangeRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(admin|member|viewer)$")


class SetFeatureFlagRequest(BaseModel):
    feature_key: str
    enabled: bool = True
    config: dict = {}


class ChangePlanRequest(BaseModel):
    plan_tier: str


class AddPermissionRequest(BaseModel):
    permission: str


def get_service(db: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(db)


# ── Org Hierarchy ────────────────────────────────────────────────────────────


@router.get("/organizations/{org_id}/tree", summary="Get organization tree")
async def get_org_tree(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        return await service.get_org_tree(org_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.post("/organizations/{org_id}/parent", summary="Set parent organization")
async def set_parent_org(
    org_id: UUID,
    request: SetParentRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "owner", user_id, db)
    try:
        org = await service.set_parent_org(org_id, request.parent_org_id, user_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {
        "id": str(org.id),
        "name": org.name,
        "parent_org_id": str(org.parent_org_id) if org.parent_org_id else None,
    }


@router.post(
    "/organizations/{org_id}/sub-orgs",
    status_code=status.HTTP_201_CREATED,
    summary="Create sub-organization",
)
async def create_sub_org(
    org_id: UUID,
    request: CreateSubOrgRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        org = await service.create_sub_org(org_id, request.name, request.slug, user_id)
    except (ValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "parent_org_id": str(org.parent_org_id),
    }


# ── Invitations ──────────────────────────────────────────────────────────────


@router.post(
    "/organizations/{org_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    summary="Invite member to organization",
)
async def invite_member(
    org_id: UUID,
    request: InviteMemberRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        inv = await service.invite_member(org_id, user_id, request.email, request.role)
    except (ValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {
        "id": str(inv.id),
        "email": inv.email,
        "role": inv.role,
        "status": inv.status,
        "created_at": inv.created_at.isoformat(),
    }


@router.get("/organizations/{org_id}/invitations", summary="List organization invitations")
async def list_invitations(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        invitations = await service.list_invitations(org_id, user_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return [
        {
            "id": str(inv.id),
            "email": inv.email,
            "role": inv.role,
            "status": inv.status,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invitations
    ]


@router.post("/invitations/{invitation_id}/accept", summary="Accept invitation")
async def accept_invitation(
    invitation_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    try:
        member = await service.accept_invitation(invitation_id, user_id)
    except (EntityNotFoundError, ForbiddenError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return {
        "id": str(member.id),
        "organization_id": str(member.organization_id),
        "role": member.role,
        "status": "accepted",
    }


@router.post("/invitations/{invitation_id}/reject", summary="Reject invitation")
async def reject_invitation(
    invitation_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
) -> dict:
    try:
        inv = await service.reject_invitation(invitation_id, user_id)
    except (EntityNotFoundError, ForbiddenError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return {"id": str(inv.id), "status": inv.status}


@router.delete(
    "/organizations/{org_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel invitation",
)
async def cancel_invitation(
    org_id: UUID,
    invitation_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        await service.cancel_invitation(invitation_id, org_id, user_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


# ── Members ──────────────────────────────────────────────────────────────────


@router.get("/organizations/{org_id}/members", summary="List organization members")
async def list_members(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        return await service.list_members(org_id, user_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


@router.patch("/organizations/{org_id}/members/{member_id}/role", summary="Change member role")
async def change_member_role(
    org_id: UUID,
    member_id: UUID,
    request: ChangeRoleRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        member = await service.change_member_role(member_id, request.role, org_id, user_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {"id": str(member.id), "role": member.role}


@router.delete(
    "/organizations/{org_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        await service.remove_member(member_id, org_id, user_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


# ── Feature Flags ────────────────────────────────────────────────────────────


@router.get("/organizations/{org_id}/features", summary="List feature flags")
async def list_feature_flags(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        flags = await service.list_feature_flags(org_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return [
        {
            "id": str(f.id),
            "feature_key": f.feature_key,
            "enabled": f.enabled,
            "config": f.config,
        }
        for f in flags
    ]


@router.put("/organizations/{org_id}/features", summary="Set feature flag")
async def set_feature_flag(
    org_id: UUID,
    request: SetFeatureFlagRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        flag = await service.set_feature_flag(
            org_id, request.feature_key, enabled=request.enabled, config=request.config
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {"id": str(flag.id), "feature_key": flag.feature_key, "enabled": flag.enabled}


@router.delete(
    "/organizations/{org_id}/features/{flag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete feature flag",
)
async def delete_feature_flag(
    org_id: UUID,
    flag_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        await service.delete_feature_flag(org_id, flag_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


# ── Usage & Billing ──────────────────────────────────────────────────────────


@router.get("/organizations/{org_id}/usage", summary="Get usage summary")
async def get_usage(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        return await service.get_usage_summary(org_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


@router.get("/organizations/{org_id}/usage/{metric}/trend", summary="Get usage trend")
async def get_usage_trend(
    org_id: UUID,
    metric: str,
    days: int = Query(30, ge=1, le=365),
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        return await service.get_usage_trend(org_id, metric, days)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None


@router.get("/organizations/{org_id}/billing", summary="Get billing plan")
async def get_billing_plan(
    org_id: UUID,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "viewer", user_id, db)
    try:
        plan = await service.get_billing_plan(org_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {
        "id": str(plan.id),
        "plan_tier": plan.plan_tier,
        "billing_cycle": plan.billing_cycle,
        "subscription_status": plan.subscription_status,
        "current_period_start": plan.current_period_start.isoformat(),
        "current_period_end": plan.current_period_end.isoformat(),
        "limits": plan.get_limits(),
    }


@router.put("/organizations/{org_id}/billing", summary="Change billing plan")
async def change_billing_plan(
    org_id: UUID,
    request: ChangePlanRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "owner", user_id, db)
    try:
        plan = await service.change_billing_plan(org_id, request.plan_tier, user_id)
    except (ValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {
        "id": str(plan.id),
        "plan_tier": plan.plan_tier,
        "subscription_status": plan.subscription_status,
    }


# ── Permissions ──────────────────────────────────────────────────────────────


@router.get("/organizations/{org_id}/check-permission/{permission}", summary="Check permission")
async def check_permission(
    org_id: UUID,
    permission: str,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "viewer", user_id, db)
    has = await service.check_permission(org_id, user_id, permission)
    return {"has_permission": has}


@router.post(
    "/organizations/{org_id}/members/{member_id}/permissions", summary="Add member permission"
)
async def add_member_permission(
    org_id: UUID,
    member_id: UUID,
    request: AddPermissionRequest,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        member = await service.add_member_permission(member_id, request.permission, org_id, user_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {"id": str(member.id), "permissions": member.permissions}


@router.delete(
    "/organizations/{org_id}/members/{member_id}/permissions/{permission}",
    summary="Remove member permission",
)
async def remove_member_permission(
    org_id: UUID,
    member_id: UUID,
    permission: str,
    service: OrganizationService = Depends(get_service),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_org_role(org_id, "admin", user_id, db)
    try:
        member = await service.remove_member_permission(member_id, permission, org_id, user_id)
    except (EntityNotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, EntityNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    return {"id": str(member.id), "permissions": member.permissions}
