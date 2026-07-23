from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.team_member import TeamMemberModel
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id

RBAC_HIERARCHY: dict[str, int] = {
    "viewer": 10,
    "member": 20,
    "admin": 30,
    "owner": 40,
}


async def require_org_role(
    organization_id: UUID,
    minimum_role: str = "member",
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberModel:
    min_level = RBAC_HIERARCHY.get(minimum_role, 0)

    result = await db.execute(
        select(TeamMemberModel).where(
            TeamMemberModel.organization_id == organization_id,
            TeamMemberModel.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    user_level = RBAC_HIERARCHY.get(member.role, 0)
    if user_level < min_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role '{minimum_role}' or higher (current: '{member.role}')",
        )

    return member
