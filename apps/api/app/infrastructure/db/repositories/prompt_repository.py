from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import SystemPromptRepository
from app.domain.entities.prompts import SystemPrompt
from app.infrastructure.db.models.prompts import SystemPromptModel


class SystemPromptRepositoryImpl(SystemPromptRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, prompt: SystemPrompt) -> SystemPrompt:
        model = SystemPromptModel.from_domain(prompt)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, prompt_id: UUID) -> SystemPrompt | None:
        result = await self.session.execute(
            select(SystemPromptModel).where(SystemPromptModel.id == prompt_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_name(self, name: str, org_id: UUID | None = None) -> SystemPrompt | None:
        stmt = select(SystemPromptModel).where(
            SystemPromptModel.name == name,
            SystemPromptModel.org_id == org_id if org_id is not None else SystemPromptModel.org_id.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def list_by_category(self, category: str, org_id: UUID | None = None) -> list[SystemPrompt]:
        stmt = select(SystemPromptModel).where(
            SystemPromptModel.category == category,
        )
        if org_id is not None:
            stmt = stmt.where(
                and_(SystemPromptModel.org_id == org_id, SystemPromptModel.status == "active")
            )
        else:
            stmt = stmt.where(SystemPromptModel.org_id.is_(None))
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    async def list_all(self, org_id: UUID | None = None) -> list[SystemPrompt]:
        stmt = select(SystemPromptModel)
        if org_id is not None:
            stmt = stmt.where(SystemPromptModel.org_id == org_id)
        else:
            stmt = stmt.where(SystemPromptModel.org_id.is_(None))
        stmt = stmt.order_by(SystemPromptModel.name)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, prompt_id: UUID) -> None:
        result = await self.session.execute(
            select(SystemPromptModel).where(SystemPromptModel.id == prompt_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
