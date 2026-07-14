"""Design Partner Repository Implementation — E6.1 Beta Launch."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.domain.entities.design_partner import (
    DesignPartner,
    DesignPartnerFeedback,
    DesignPartnerStatus,
    DesignPartnerTier,
    FeedbackStatus,
    FeedbackType,
)
from app.infrastructure.db.base import Base


class DesignPartnerModel(Base):
    __tablename__ = "design_partners"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier = Column(String(50), default=DesignPartnerTier.DESIGN_PARTNER.value, nullable=False)
    status = Column(String(50), default=DesignPartnerStatus.PENDING.value, nullable=False, index=True)

    dedicated_csm_id = Column(PG_UUID(as_uuid=True), nullable=True)

    contract_signed_at = Column(DateTime(timezone=True), nullable=True)
    contract_expires_at = Column(DateTime(timezone=True), nullable=True)
    custom_terms = Column(String(50), default="{}", nullable=False)  # JSON

    billing_contact_email = Column(String(255), nullable=True)
    custom_pricing = Column(String(50), default="{}", nullable=False)  # JSON

    onboarding_started_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_milestones = Column(String(50), default="[]", nullable=False)  # JSON
    onboarding_csm_id = Column(PG_UUID(as_uuid=True), nullable=True)

    weekly_active_users = Column(String(20), default="0", nullable=False)
    campaigns_run = Column(String(20), default="0", nullable=False)
    ai_interactions = Column(String(20), default="0", nullable=False)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)

    nps_score = Column(String(20), nullable=True)
    nps_reason = Column(Text, nullable=True)
    nps_responded_at = Column(DateTime(timezone=True), nullable=True)

    feedback_count = Column(String(20), default="0", nullable=False)
    feedback_by_type = Column(String(50), default="{}", nullable=False)  # JSON

    support_tier = Column(String(50), default="standard", nullable=False)
    open_tickets = Column(String(20), default="0", nullable=False)
    avg_resolution_hours = Column(String(20), default="0.0", nullable=False)

    notes = Column(Text, default="", nullable=False)
    internal_tags = Column(String(50), default="[]", nullable=False)  # JSON

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)


class DesignPartnerFeedbackModel(Base):
    __tablename__ = "design_partner_feedback"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    design_partner_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("design_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)

    type = Column(String(50), nullable=False)
    priority = Column(String(50), default=FeedbackPriority.MEDIUM.value, nullable=False)
    status = Column(String(50), default=FeedbackStatus.OPEN.value, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    feature_area = Column(String(100), nullable=True)
    related_entity_type = Column(String(100), nullable=True)
    related_entity_id = Column(String(100), nullable=True)

    nps_score = Column(String(10), nullable=True)
    nps_reason = Column(Text, nullable=True)

    assigned_to = Column(PG_UUID(as_uuid=True), nullable=True)
    triaged_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, default="", nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    tags = Column(String(50), default="[]", nullable=False)  # JSON
    metadata = Column(String(50), default="{}", nullable=False)  # JSON

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DesignPartnerRepositoryImpl:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model: DesignPartnerModel) -> DesignPartner:
        import json
        return DesignPartner(
            id=model.id,
            organization_id=model.organization_id,
            tier=DesignPartnerTier(model.tier),
            status=DesignPartnerStatus(model.status),
            dedicated_csm_id=model.dedicated_csm_id,
            contract_signed_at=model.contract_signed_at,
            contract_expires_at=model.contract_expires_at,
            custom_terms=json.loads(model.custom_terms) if model.custom_terms else {},
            billing_contact_email=model.billing_contact_email,
            custom_pricing=json.loads(model.custom_pricing) if model.custom_pricing else {},
            onboarding_started_at=model.onboarding_started_at,
            onboarding_completed_at=model.onboarding_completed_at,
            onboarding_milestones=json.loads(model.onboarding_milestones) if model.onboarding_milestones else [],
            onboarding_csm_id=model.onboarding_csm_id,
            weekly_active_users=int(model.weekly_active_users) if model.weekly_active_users else 0,
            campaigns_run=int(model.campaigns_run) if model.campaigns_run else 0,
            ai_interactions=int(model.ai_interactions) if model.ai_interactions else 0,
            last_engagement_at=model.last_engagement_at,
            nps_score=int(model.nps_score) if model.nps_score else None,
            nps_reason=model.nps_reason,
            nps_responded_at=model.nps_responded_at,
            feedback_count=int(model.feedback_count) if model.feedback_count else 0,
            feedback_by_type=json.loads(model.feedback_by_type) if model.feedback_by_type else {},
            support_tier=model.support_tier,
            open_tickets=int(model.open_tickets) if model.open_tickets else 0,
            avg_resolution_hours=float(model.avg_resolution_hours) if model.avg_resolution_hours else 0.0,
            notes=model.notes,
            internal_tags=json.loads(model.internal_tags) if model.internal_tags else [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            approved_at=model.approved_at,
            activated_at=model.activated_at,
        )

    def _entity_to_model(self, entity: DesignPartner) -> DesignPartnerModel:
        import json
        return DesignPartnerModel(
            id=entity.id,
            organization_id=entity.organization_id,
            tier=entity.tier.value,
            status=entity.status.value,
            dedicated_csm_id=entity.dedicated_csm_id,
            contract_signed_at=entity.contract_signed_at,
            contract_expires_at=entity.contract_expires_at,
            custom_terms=json.dumps(entity.custom_terms),
            billing_contact_email=entity.billing_contact_email,
            custom_pricing=json.dumps(entity.custom_pricing),
            onboarding_started_at=entity.onboarding_started_at,
            onboarding_completed_at=entity.onboarding_completed_at,
            onboarding_milestones=json.dumps(entity.onboarding_milestones),
            onboarding_csm_id=entity.onboarding_csm_id,
            weekly_active_users=str(entity.weekly_active_users),
            campaigns_run=str(entity.campaigns_run),
            ai_interactions=str(entity.ai_interactions),
            last_engagement_at=entity.last_engagement_at,
            nps_score=str(entity.nps_score) if entity.nps_score else None,
            nps_reason=entity.nps_reason,
            nps_responded_at=entity.nps_responded_at,
            feedback_count=str(entity.feedback_count),
            feedback_by_type=json.dumps(entity.feedback_by_type),
            support_tier=entity.support_tier,
            open_tickets=str(entity.open_tickets),
            avg_resolution_hours=str(entity.avg_resolution_hours),
            notes=entity.notes,
            internal_tags=json.dumps(entity.internal_tags),
        )

    async def save(self, partner: DesignPartner) -> DesignPartner:
        model = self._entity_to_model(partner)
        existing = await self.db.get(DesignPartnerModel, model.id)
        if existing:
            for attr in (
                "tier", "status", "dedicated_csm_id", "contract_signed_at", "contract_expires_at",
                "custom_terms", "billing_contact_email", "custom_pricing", "onboarding_started_at",
                "onboarding_completed_at", "onboarding_milestones", "onboarding_csm_id",
                "weekly_active_users", "campaigns_run", "ai_interactions", "last_engagement_at",
                "nps_score", "nps_reason", "nps_responded_at", "feedback_count",
                "feedback_by_type", "support_tier", "open_tickets", "avg_resolution_hours",
                "notes", "internal_tags", "updated_at", "approved_at", "activated_at",
            ):
                setattr(existing, attr, getattr(model, attr))
            model = existing
        else:
            self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return self._model_to_entity(model)

    async def find_by_id(self, partner_id: UUID) -> DesignPartner | None:
        result = await self.db.execute(
            select(DesignPartnerModel).where(DesignPartnerModel.id == partner_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def find_by_organization(self, org_id: UUID) -> DesignPartner | None:
        result = await self.db.execute(
            select(DesignPartnerModel).where(DesignPartnerModel.organization_id == org_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def list_all(
        self,
        status: DesignPartnerStatus | None = None,
        tier: DesignPartnerTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DesignPartner]:
        query = select(DesignPartnerModel)
        if status:
            query = query.where(DesignPartnerModel.status == status.value)
        if tier:
            query = query.where(DesignPartnerModel.tier == tier.value)
        query = query.order_by(DesignPartnerModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def count(self, status: DesignPartnerStatus | None = None) -> int:
        from sqlalchemy import func
        query = select(func.count(DesignPartnerModel.id))
        if status:
            query = query.where(DesignPartnerModel.status == status.value)
        result = await self.db.execute(query)
        return result.scalar_one() or 0


class DesignPartnerFeedbackRepositoryImpl:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model: DesignPartnerFeedbackModel) -> DesignPartnerFeedback:
        import json
        return DesignPartnerFeedback(
            id=model.id,
            design_partner_id=model.design_partner_id,
            organization_id=model.organization_id,
            user_id=model.user_id,
            type=FeedbackType(model.type),
            priority=model.priority,
            status=model.status,
            title=model.title,
            description=model.description,
            feature_area=model.feature_area,
            related_entity_type=model.related_entity_type,
            related_entity_id=model.related_entity_id,
            nps_score=int(model.nps_score) if model.nps_score else None,
            nps_reason=model.nps_reason,
            assigned_to=model.assigned_to,
            triaged_at=model.triaged_at,
            resolution_notes=model.resolution_notes,
            resolved_at=model.resolved_at,
            tags=json.loads(model.tags) if model.tags else [],
            metadata=json.loads(model.metadata) if model.metadata else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: DesignPartnerFeedback) -> DesignPartnerFeedbackModel:
        import json
        return DesignPartnerFeedbackModel(
            id=entity.id,
            design_partner_id=entity.design_partner_id,
            organization_id=entity.organization_id,
            user_id=entity.user_id,
            type=entity.type.value,
            priority=entity.priority.value,
            status=entity.status.value,
            title=entity.title,
            description=entity.description,
            feature_area=entity.feature_area,
            related_entity_type=entity.related_entity_type,
            related_entity_id=entity.related_entity_id,
            nps_score=str(entity.nps_score) if entity.nps_score else None,
            nps_reason=entity.nps_reason,
            assigned_to=entity.assigned_to,
            triaged_at=entity.triaged_at,
            resolution_notes=entity.resolution_notes,
            resolved_at=entity.resolved_at,
            tags=json.dumps(entity.tags),
            metadata=json.dumps(entity.metadata),
        )

    async def save(self, feedback: DesignPartnerFeedback) -> DesignPartnerFeedback:
        model = self._entity_to_model(feedback)
        existing = await self.db.get(DesignPartnerFeedbackModel, model.id)
        if existing:
            for attr in (
                "type", "priority", "status", "title", "description", "feature_area",
                "related_entity_type", "related_entity_id", "nps_score", "nps_reason",
                "assigned_to", "triaged_at", "resolution_notes", "resolved_at",
                "tags", "metadata", "updated_at",
            ):
                setattr(existing, attr, getattr(model, attr))
            model = existing
        else:
            self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return self._model_to_entity(model)

    async def find_by_id(self, feedback_id: UUID) -> DesignPartnerFeedback | None:
        result = await self.db.execute(
            select(DesignPartnerFeedbackModel).where(DesignPartnerFeedbackModel.id == feedback_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def find_by_partner(
        self,
        partner_id: UUID,
        status: str | None = None,
        type: str | None = None,
        limit: int = 50,
    ) -> list[DesignPartnerFeedback]:
        query = select(DesignPartnerFeedbackModel).where(
            DesignPartnerFeedbackModel.design_partner_id == partner_id
        )
        if status:
            query = query.where(DesignPartnerFeedbackModel.status == status)
        if type:
            query = query.where(DesignPartnerFeedbackModel.type == type)
        query = query.order_by(DesignPartnerFeedbackModel.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_all(
        self,
        status: str | None = None,
        type: str | None = None,
        priority: str | None = None,
        limit: int = 50,
    ) -> list[DesignPartnerFeedback]:
        query = select(DesignPartnerFeedbackModel)
        if status:
            query = query.where(DesignPartnerFeedbackModel.status == status)
        if type:
            query = query.where(DesignPartnerFeedbackModel.type == type)
        if priority:
            query = query.where(DesignPartnerFeedbackModel.priority == priority)
        query = query.order_by(DesignPartnerFeedbackModel.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
