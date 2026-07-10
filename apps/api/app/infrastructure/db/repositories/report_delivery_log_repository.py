from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.reports.report_template import ReportDeliveryLog
from app.infrastructure.db.models.report_template import ReportDeliveryLogModel


class ReportDeliveryLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, log: ReportDeliveryLog) -> ReportDeliveryLog:
        model = ReportDeliveryLogModel.from_domain(log)
        self.session.add(model)
        await self.session.flush()
        return model.to_domain()

    async def find_by_organization(self, org_id: UUID) -> list[ReportDeliveryLog]:
        result = await self.session.execute(
            select(ReportDeliveryLogModel)
            .where(ReportDeliveryLogModel.organization_id == org_id)
            .order_by(ReportDeliveryLogModel.generated_at.desc())
        )
        return [m.to_domain() for m in result.scalars().all()]

    async def find_by_id(self, log_id: UUID) -> ReportDeliveryLog | None:
        result = await self.session.execute(
            select(ReportDeliveryLogModel).where(ReportDeliveryLogModel.id == log_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None
