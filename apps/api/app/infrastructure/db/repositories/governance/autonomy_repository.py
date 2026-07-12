"""Autonomy repository implementations — DB adapter for autonomy entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.governance.autonomy_use_cases import (
    AgentActionRepository,
    AutonomyConfigRepository,
)
from app.domain.entities.governance.autonomy import AgentAction, AutonomyConfig
from app.infrastructure.db.models.governance.agent_action_model import (
    AgentActionModel,
)
from app.infrastructure.db.models.governance.autonomy_config_model import (
    AutonomyConfigModel,
)


class AutonomyConfigRepositoryImpl(AutonomyConfigRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, config: AutonomyConfig) -> AutonomyConfig:
        model = AutonomyConfigModel.from_domain(config)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_organization(self, org_id: UUID) -> AutonomyConfig | None:
        result = await self.session.execute(
            select(AutonomyConfigModel).where(
                AutonomyConfigModel.organization_id == str(org_id)
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None


class AgentActionRepositoryImpl(AgentActionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, action: AgentAction) -> AgentAction:
        model = AgentActionModel.from_domain(action)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_id(self, action_id: UUID) -> AgentAction | None:
        result = await self.session.execute(
            select(AgentActionModel).where(
                AgentActionModel.id == str(action_id)
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(
        self,
        org_id: UUID,
        agent_type: str | None = None,
        action_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentAction]:
        query = select(AgentActionModel).where(
            AgentActionModel.organization_id == str(org_id)
        )
        if agent_type:
            query = query.where(AgentActionModel.agent_type == agent_type)
        if action_name:
            query = query.where(AgentActionModel.action == action_name)
        query = query.order_by(AgentActionModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def find_by_agent(
        self,
        org_id: UUID,
        agent_id: str,
        limit: int = 50,
    ) -> list[AgentAction]:
        result = await self.session.execute(
            select(AgentActionModel).where(
                AgentActionModel.organization_id == str(org_id),
                AgentActionModel.agent_id == agent_id,
            ).order_by(AgentActionModel.created_at.desc()).limit(limit)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]
