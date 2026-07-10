from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.dashboards.dashboard import Dashboard, DashboardWidget
from app.infrastructure.db.models.dashboards.dashboard_model import (
    DashboardModel,
    DashboardWidgetModel,
)


class DashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, dashboard: Dashboard) -> Dashboard:
        model = DashboardModel.from_domain(dashboard)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, dashboard_id: UUID) -> Dashboard | None:
        result = await self.session.execute(
            select(DashboardModel).where(DashboardModel.id == dashboard_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(self, org_id: UUID) -> list[Dashboard]:
        result = await self.session.execute(
            select(DashboardModel)
            .where(DashboardModel.organization_id == org_id)
            .order_by(DashboardModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_default(self, org_id: UUID) -> Dashboard | None:
        result = await self.session.execute(
            select(DashboardModel)
            .where(DashboardModel.organization_id == org_id, DashboardModel.is_default)
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def delete(self, dashboard_id: UUID) -> None:
        await self.session.execute(
            DashboardWidgetModel.__table__.delete().where(
                DashboardWidgetModel.dashboard_id == dashboard_id
            )
        )
        model = await self.session.get(DashboardModel, dashboard_id)
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()


class DashboardWidgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, widget: DashboardWidget) -> DashboardWidget:
        model = DashboardWidgetModel.from_domain(widget)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_dashboard(self, dashboard_id: UUID) -> list[DashboardWidget]:
        result = await self.session.execute(
            select(DashboardWidgetModel)
            .where(DashboardWidgetModel.dashboard_id == dashboard_id)
            .order_by(DashboardWidgetModel.pos_y, DashboardWidgetModel.pos_x)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_dashboard_ids(self, dashboard_ids: list[UUID]) -> list[DashboardWidget]:
        if not dashboard_ids:
            return []
        result = await self.session.execute(
            select(DashboardWidgetModel)
            .where(DashboardWidgetModel.dashboard_id.in_(dashboard_ids))
            .order_by(DashboardWidgetModel.dashboard_id, DashboardWidgetModel.pos_y, DashboardWidgetModel.pos_x)
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_id(self, widget_id: UUID) -> DashboardWidget | None:
        result = await self.session.execute(
            select(DashboardWidgetModel).where(DashboardWidgetModel.id == widget_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def delete(self, widget_id: UUID) -> None:
        model = await self.session.get(DashboardWidgetModel, widget_id)
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()

    async def delete_by_dashboard(self, dashboard_id: UUID) -> None:
        await self.session.execute(
            DashboardWidgetModel.__table__.delete().where(
                DashboardWidgetModel.dashboard_id == dashboard_id
            )
        )
        await self.session.flush()
