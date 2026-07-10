from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.monitoring.audit_log import AuditLogEntry
from app.infrastructure.db.models.monitoring.audit_log_model import AuditLogEntryModel


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: UUID | None = None,
        organization_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        entry = AuditLogEntry(
            organization_id=organization_id or uuid4(),
            user_id=actor_id or uuid4(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=metadata or {},
            ip_address="",
        )
        model = AuditLogEntryModel.from_domain(entry)
        self.session.add(model)
        await self.session.flush()
