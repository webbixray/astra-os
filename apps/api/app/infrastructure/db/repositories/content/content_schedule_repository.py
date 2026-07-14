"""Content Schedule Repository — Data access for recurring content schedules."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.content.content_schedule import ContentSchedule
from app.infrastructure.db.models.content.content_schedule_model import ContentScheduleModel


class ContentScheduleRepository:
    """Repository for ContentSchedule entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, schedule: ContentSchedule) -> ContentSchedule:
        """Save or update a schedule."""
        model = ContentScheduleModel.from_domain(schedule)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, schedule_id: UUID) -> ContentSchedule | None:
        """Find schedule by ID."""
        result = await self.session.execute(
            select(ContentScheduleModel).where(ContentScheduleModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_content(self, content_id: UUID) -> list[ContentSchedule]:
        """Find all schedules for a content item."""
        result = await self.session.execute(
            select(ContentScheduleModel)
            .where(ContentScheduleModel.content_id == content_id)
            .order_by(ContentScheduleModel.created_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_organization(
        self, organization_id: UUID, status: str | None = None
    ) -> list[ContentSchedule]:
        """Find all schedules for an organization."""
        query = select(ContentScheduleModel).where(
            ContentScheduleModel.organization_id == organization_id
        )
        if status is not None:
            query = query.where(ContentScheduleModel.status == status)
        query = query.order_by(ContentScheduleModel.next_run_at.asc().nullslast())
        result = await self.session.execute(query)
        return [m.to_domain() for m in result.scalars().all()]

    async def find_due_schedules(self, current_time: datetime | None = None) -> list[ContentSchedule]:
        """Find all active schedules that are due to run."""
        current = current_time or datetime.now(UTC)
        result = await self.session.execute(
            select(ContentScheduleModel)
            .where(
                ContentScheduleModel.status == "active",
                ContentScheduleModel.next_run_at <= current,
            )
            .order_by(ContentScheduleModel.next_run_at.asc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def delete(self, schedule_id: UUID) -> None:
        """Delete a schedule."""
        result = await self.session.execute(
            select(ContentScheduleModel).where(ContentScheduleModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()
