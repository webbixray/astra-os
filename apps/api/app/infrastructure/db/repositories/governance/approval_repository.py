"""Approval repository implementations — DB adapter for approval entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.governance.approval_use_cases import (
    ApprovalDecisionRepository,
    ApprovalRequestRepository,
    ApprovalRuleRepository,
)
from app.domain.entities.governance.approval import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalRule,
)
from app.infrastructure.db.models.governance.approval_decision_model import (
    ApprovalDecisionModel,
)
from app.infrastructure.db.models.governance.approval_request_model import (
    ApprovalRequestModel,
)
from app.infrastructure.db.models.governance.approval_rule_model import (
    ApprovalRuleModel,
)


class ApprovalRuleRepositoryImpl(ApprovalRuleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, rule: ApprovalRule) -> ApprovalRule:
        model = ApprovalRuleModel.from_domain(rule)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, rule_id: UUID) -> ApprovalRule | None:
        result = await self.session.execute(
            select(ApprovalRuleModel).where(ApprovalRuleModel.id == str(rule_id))
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_by_organization(
        self, org_id: UUID, active_only: bool = True
    ) -> list[ApprovalRule]:
        query = select(ApprovalRuleModel).where(
            ApprovalRuleModel.organization_id == str(org_id)
        )
        if active_only:
            query = query.where(ApprovalRuleModel.is_active == True)  # noqa: E712
        query = query.order_by(ApprovalRuleModel.priority.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def delete(self, rule_id: UUID) -> None:
        result = await self.session.execute(
            select(ApprovalRuleModel).where(ApprovalRuleModel.id == str(rule_id))
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self.session.delete(model)
            await self.session.flush()


class ApprovalRequestRepositoryImpl(ApprovalRequestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, request: ApprovalRequest) -> ApprovalRequest:
        model = ApprovalRequestModel.from_domain(request)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_id(self, request_id: UUID) -> ApprovalRequest | None:
        result = await self.session.execute(
            select(ApprovalRequestModel).where(
                ApprovalRequestModel.id == str(request_id)
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None

    async def find_pending_by_organization(
        self, org_id: UUID
    ) -> list[ApprovalRequest]:
        result = await self.session.execute(
            select(ApprovalRequestModel).where(
                ApprovalRequestModel.organization_id == str(org_id),
                ApprovalRequestModel.status == "pending",
            ).order_by(ApprovalRequestModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def find_pending_by_role(
        self, org_id: UUID, role: str
    ) -> list[ApprovalRequest]:
        result = await self.session.execute(
            select(ApprovalRequestModel).where(
                ApprovalRequestModel.organization_id == str(org_id),
                ApprovalRequestModel.status == "pending",
                ApprovalRequestModel.assigned_role == role,
            ).order_by(ApprovalRequestModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def find_expired_stale(self, before: datetime) -> list[ApprovalRequest]:
        result = await self.session.execute(
            select(ApprovalRequestModel).where(
                ApprovalRequestModel.status == "pending",
                ApprovalRequestModel.timeout_at <= before.isoformat(),
            )
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]


class ApprovalDecisionRepositoryImpl(ApprovalDecisionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, decision: ApprovalDecision) -> ApprovalDecision:
        model = ApprovalDecisionModel.from_domain(decision)
        merged = await self.session.merge(model)
        await self.session.flush()
        return merged.to_domain()

    async def find_by_request_id(
        self, request_id: UUID
    ) -> ApprovalDecision | None:
        result = await self.session.execute(
            select(ApprovalDecisionModel).where(
                ApprovalDecisionModel.request_id == str(request_id)
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model is not None else None
