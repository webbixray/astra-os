"""Casbin-based RBAC dependencies for FastAPI."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.team_member import TeamMemberModel
from app.infrastructure.security.casbin import get_enforcer
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id


async def get_user_roles(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Get user's roles in the organization."""
    result = await db.execute(
        select(TeamMemberModel.role).where(
            TeamMemberModel.organization_id == organization_id,
            TeamMemberModel.user_id == user_id,
        )
    )
    roles = [row[0] for row in result.all()]
    if not roles:
        roles = ["viewer"]  # Default role if not explicitly a member
    return roles


def require_permission(resource: str, action: str):
    """Dependency factory for checking Casbin permissions.

    Args:
        resource: Resource name (e.g., "campaigns", "organizations", "agents")
        action: Action name (e.g., "read", "write", "create", "update", "delete", "*")

    Returns:
        FastAPI dependency that checks permission

    """

    async def _check_permission(
        organization_id: UUID,
        user_roles: list[str] = Depends(get_user_roles),
        enforcer=Depends(get_enforcer),
    ) -> list[str]:
        # Check if any of the user's roles have the permission
        for role in user_roles:
            if enforcer.enforce(role, resource, action):
                return user_roles

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: requires '{action}' on '{resource}'",
        )

    return _check_permission


async def require_org_role(
    organization_id: UUID,
    minimum_role: str = "member",
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberModel:
    """Require user to have at least the specified role in the organization.

    This is the legacy RBAC check, kept for backward compatibility.
    """
    from app.presentation.middleware.rbac import RBAC_HIERARCHY

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
