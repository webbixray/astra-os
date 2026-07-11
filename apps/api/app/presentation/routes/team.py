from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.team_member import TeamMember
from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl
from app.presentation.dependencies import get_db, get_member_repo, get_user_repo, pagination_params
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.schemas.common import PaginatedResponse

router = APIRouter()


class InviteRequest(BaseModel):
    organization_id: UUID
    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(admin|member|viewer)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    name: str
    role: str
    joined_at: str | None = None


@router.post("/teams/invite", status_code=201)
async def invite_member(
    request: InviteRequest,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepositoryImpl = Depends(get_user_repo),
    member_repo: TeamMemberRepositoryImpl = Depends(get_member_repo),
    current_user_id: UUID = Depends(require_user_id),
) -> dict:
    await require_org_role(request.organization_id, "admin", current_user_id, db)

    invited_user = await user_repo.find_by_email(request.email)
    if invited_user is None:
        raise HTTPException(status_code=404, detail="User not found. Ask them to sign up first.")

    existing = await member_repo.find_by_user_and_organization(
        invited_user.id, request.organization_id
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="User is already a member")

    member = TeamMember.create(
        organization_id=request.organization_id,
        user_id=invited_user.id,
        role=request.role,
    )
    saved = await member_repo.save(member)

    return {
        "id": str(saved.id),
        "user_id": str(saved.user_id),
        "role": saved.role,
        "status": "invited",
    }


@router.get("/teams/members", response_model=PaginatedResponse[MemberResponse])
async def list_members(
    organization_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_user_id),
    pagination: dict = Depends(pagination_params),
) -> PaginatedResponse:
    await require_org_role(organization_id, "viewer", current_user_id, db)

    stmt = select(
        TeamMemberModel,
        UserModel.email,
        UserModel.name,
    ).join(
        UserModel, TeamMemberModel.user_id == UserModel.id
    ).where(
        TeamMemberModel.organization_id == organization_id,
    )

    result = await db.execute(stmt)
    rows = result.all()

    items = [
        MemberResponse(
            id=str(m.TeamMemberModel.id),
            user_id=str(m.TeamMemberModel.user_id),
            email=m.email,
            name=m.name,
            role=m.TeamMemberModel.role,
            joined_at=m.TeamMemberModel.joined_at.isoformat() if m.TeamMemberModel.joined_at else None,
        )
        for m in rows
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


@router.patch("/teams/members/{member_id}/role")
async def update_member_role(
    member_id: UUID,
    request: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    member_repo: TeamMemberRepositoryImpl = Depends(get_member_repo),
    current_user_id: UUID = Depends(require_user_id),
) -> dict:
    member = await member_repo.find_by_id(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    await require_org_role(member.organization_id, "admin", current_user_id, db)

    if request.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot assign owner role via this endpoint")

    member.change_role(request.role)
    saved = await member_repo.save(member)

    return {"id": str(saved.id), "role": saved.role}


@router.delete("/teams/members/{member_id}", status_code=204)
async def remove_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    member_repo: TeamMemberRepositoryImpl = Depends(get_member_repo),
    current_user_id: UUID = Depends(require_user_id),
) -> None:
    member = await member_repo.find_by_id(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    await require_org_role(member.organization_id, "admin", current_user_id, db)

    if member.user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    await member_repo.delete(member_id)
