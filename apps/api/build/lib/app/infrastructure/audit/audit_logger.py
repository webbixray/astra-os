from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.monitoring.audit_log_model import AuditLogEntryModel

logger = structlog.get_logger(__name__)


class AuditLogger:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        user_id: UUID,
        details: dict | None = None,
        organization_id: UUID | None = None,
    ) -> AuditLogEntryModel:
        entry = AuditLogEntryModel(
            organization_id=organization_id or UUID(int=0),
            user_id=user_id,
            action=event_type,
            resource_type=entity_type,
            resource_id=str(entity_id),
            details=details or {},
        )
        self.db.add(entry)
        await self.db.flush()

        logger.info(
            "audit_event",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            user_id=str(user_id),
            organization_id=str(organization_id) if organization_id else None,
        )

        return entry
