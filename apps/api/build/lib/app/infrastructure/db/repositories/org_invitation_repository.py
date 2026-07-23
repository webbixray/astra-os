from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.organization import OrgInvitation
from app.infrastructure.db.models.org_invitation import OrgInvitationModel


class OrgInvitationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, invitation: OrgInvitation) -> OrgInvitation:
        model = OrgInvitationModel.from_domain(invitation)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, invitation_id: UUID) -> OrgInvitation | None:
        result = await self.session.execute(
            select(OrgInvitationModel).where(OrgInvitationModel.id == invitation_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID) -> list[OrgInvitation]:
        result = await self.session.execute(
            select(OrgInvitationModel)
            .where(OrgInvitationModel.organization_id == org_id)
            .order_by(OrgInvitationModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_pending_by_email(self, email: str) -> list[OrgInvitation]:
        result = await self.session.execute(
            select(OrgInvitationModel)
            .where(
                OrgInvitationModel.email == email,
                OrgInvitationModel.status == "pending",
            )
            .order_by(OrgInvitationModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, invitation_id: UUID) -> None:
        model = await self.session.get(OrgInvitationModel, invitation_id)
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
