"""Design Partner Service — E6.1 Beta Launch.

Service for managing enterprise design partners, feedback loops, and dedicated support.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.domain.common import now
from app.domain.entities.design_partner import (
    DesignPartner,
    DesignPartnerFeedback,
    DesignPartnerFeedbackRepository,
    DesignPartnerRepository,
    DesignPartnerStatus,
    DesignPartnerTier,
    FeedbackPriority,
    FeedbackType,
    SupportTicket,
)


class DesignPartnerService:
    """Service for managing design partners."""

    def __init__(
        self,
        repo: DesignPartnerRepository,
        feedback_repo: DesignPartnerFeedbackRepository,
    ) -> None:
        self.repo = repo
        self.feedback_repo = feedback_repo

    # --- Design Partner CRUD ---

    async def create_partner(
        self,
        organization_id: UUID,
        tier: DesignPartnerTier = DesignPartnerTier.DESIGN_PARTNER,
        dedicated_csm_id: UUID | None = None,
        contract_expires_at: datetime | None = None,
        custom_terms: dict[str, Any] | None = None,
        support_tier: str = "priority",
        notes: str = "",
        tags: list[str] | None = None,
    ) -> DesignPartner:
        """Create a new design partner record."""
        partner = DesignPartner(
            organization_id=organization_id,
            tier=tier,
            dedicated_csm_id=dedicated_csm_id,
            contract_expires_at=contract_expires_at or (now() + timedelta(days=365)),
            custom_terms=custom_terms or {},
            support_tier=support_tier,
            notes=notes,
            internal_tags=tags or [],
        )
        partner.status = DesignPartnerStatus.PENDING
        return await self.repo.save(partner)

    async def approve_partner(
        self,
        partner_id: UUID,
        approved_by: UUID,
        contract_signed_at: datetime | None = None,
    ) -> DesignPartner:
        """Approve a design partner and move to onboarding."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.status = DesignPartnerStatus.APPROVED
        partner.approved_at = now()
        partner.contract_signed_at = contract_signed_at or now()
        partner.updated_at = now()
        return await self.repo.save(partner)

    async def start_onboarding(self, partner_id: UUID, csm_id: UUID) -> DesignPartner:
        """Start the onboarding process for a design partner."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.start_onboarding(csm_id)
        return await self.repo.save(partner)

    async def complete_onboarding(self, partner_id: UUID) -> DesignPartner:
        """Complete onboarding and activate the partner."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.complete_onboarding()
        return await self.repo.save(partner)

    async def add_milestone(self, partner_id: UUID, milestone: str) -> DesignPartner:
        """Add an onboarding milestone."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.add_milestone(milestone)
        return await self.repo.save(partner)

    async def get_partner(self, partner_id: UUID) -> DesignPartner | None:
        return await self.repo.find_by_id(partner_id)

    async def get_partner_by_org(self, org_id: UUID) -> DesignPartner | None:
        return await self.repo.find_by_organization(org_id)

    async def list_partners(
        self,
        status: DesignPartnerStatus | None = None,
        tier: DesignPartnerTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DesignPartner]:
        return await self.repo.list_all(status=status, tier=tier, limit=limit, offset=offset)

    async def count_partners(self, status: DesignPartnerStatus | None = None) -> int:
        return await self.repo.count(status=status)

    async def update_partner(
        self,
        partner_id: UUID,
        updates: dict[str, Any],
    ) -> DesignPartner:
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        for key, value in updates.items():
            if hasattr(partner, key) and key not in ("id", "organization_id", "created_at"):
                setattr(partner, key, value)

        partner.updated_at = now()
        return await self.repo.save(partner)

    async def record_engagement(
        self,
        partner_id: UUID,
        wau: int = 0,
        campaigns: int = 0,
        ai_interactions: int = 0,
    ) -> DesignPartner:
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.update_engagement(wau=wau, campaigns=campaigns, ai_interactions=ai_interactions)
        return await self.repo.save(partner)

    async def update_nps(self, partner_id: UUID, score: int) -> DesignPartner:
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        partner.update_nps(score)
        return await self.repo.save(partner)

    # --- Feedback Management ---

    async def submit_feedback(
        self,
        partner_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        feature_area: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        nps_score: int | None = None,
        nps_reason: str | None = None,
        tags: list[str] | None = None,
    ) -> DesignPartnerFeedback:
        """Submit feedback from a design partner."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        feedback = DesignPartnerFeedback(
            design_partner_id=partner_id,
            organization_id=organization_id,
            user_id=user_id,
            type=feedback_type,
            priority=priority,
            title=title,
            description=description,
            feature_area=feature_area,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            nps_score=nps_score,
            nps_reason=nps_reason,
            tags=tags or [],
        )

        # Update partner stats
        partner.record_feedback(feedback_type)
        if feedback_type == FeedbackType.NPS_SURVEY and nps_score is not None:
            partner.update_nps(nps_score)
        await self.repo.save(partner)

        return await self.feedback_repo.save(feedback)

    async def get_feedback(
        self,
        feedback_id: UUID,
    ) -> DesignPartnerFeedback | None:
        return await self.feedback_repo.find_by_id(feedback_id)

    async def list_feedback(
        self,
        partner_id: UUID,
        status: str | None = None,
        type: FeedbackType | None = None,
        limit: int = 50,
    ) -> list[DesignPartnerFeedback]:
        return await self.feedback_repo.find_by_partner(
            partner_id, status=status, type=type, limit=limit
        )

    async def triage_feedback(
        self,
        feedback_id: UUID,
        assignee_id: UUID,
        priority: FeedbackPriority | None = None,
    ) -> DesignPartnerFeedback:
        feedback = await self.feedback_repo.find_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")

        feedback.triage(assignee_id)
        if priority:
            feedback.priority = priority

        return await self.feedback_repo.save(feedback)

    async def resolve_feedback(
        self,
        feedback_id: UUID,
        resolution_notes: str = "",
    ) -> DesignPartnerFeedback:
        feedback = await self.feedback_repo.find_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")

        feedback.resolve(resolution_notes)
        return await self.feedback_repo.save(feedback)

    # --- Support Tickets ---

    async def create_ticket(
        self,
        partner_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        subject: str,
        description: str,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        channel: str = "email",
        sla_tier: str = "standard",
    ) -> SupportTicket:
        """Create a support ticket for a design partner."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        # Calculate SLA due dates based on tier
        sla_hours = {"standard": 24, "priority": 8, "dedicated": 4}
        first_response_hours = {"standard": 4, "priority": 2, "dedicated": 1}

        now_dt = now()
        first_response_due = now_dt + timedelta(hours=first_response_hours.get(sla_tier, 4))
        resolution_due = now_dt + timedelta(hours=sla_hours.get(sla_tier, 24))

        ticket = SupportTicket(
            design_partner_id=partner_id,
            organization_id=organization_id,
            user_id=user_id,
            subject=subject,
            description=description,
            priority=FeedbackPriority.HIGH if priority == FeedbackPriority.CRITICAL else priority,
            channel=channel,
            sla_tier=sla_tier,
            first_response_due_at=first_response_due,
            resolution_due_at=resolution_due,
        )

        partner.open_tickets += 1
        await self.repo.save(partner)

        return ticket

    async def assign_ticket(self, ticket_id: UUID, csm_id: UUID) -> SupportTicket:
        """Assign a support ticket to a CSM."""
        # In a real implementation, this would fetch from a ticket repo
        # For now, returning a mock ticket
        raise NotImplementedError("Ticket repository not implemented yet")

    async def respond_to_ticket(self, ticket_id: UUID) -> SupportTicket:
        """Mark first response on a ticket."""
        raise NotImplementedError("Ticket repository not implemented yet")

    async def resolve_ticket(
        self,
        ticket_id: UUID,
        resolution_summary: str,
        satisfaction: int | None = None,
    ) -> SupportTicket:
        """Resolve a support ticket."""
        raise NotImplementedError("Ticket repository not implemented yet")

    # --- Analytics ---

    async def get_partner_stats(self, partner_id: UUID) -> dict[str, Any]:
        """Get comprehensive stats for a design partner."""
        partner = await self.repo.find_by_id(partner_id)
        if not partner:
            raise ValueError(f"Design partner {partner_id} not found")

        feedback = await self.feedback_repo.find_by_partner(partner_id, limit=100)

        return {
            "partner": partner.to_dict(),
            "feedback": {
                "total": len(feedback),
                "open": sum(1 for f in feedback if f.status == "open"),
                "resolved": sum(1 for f in feedback if f.status == "resolved"),
                "by_type": {},
                "by_priority": {},
            },
            "engagement": {
                "weekly_active_users": partner.weekly_active_users,
                "campaigns_run": partner.campaigns_run,
                "ai_interactions": partner.ai_interactions,
                "last_engagement": partner.last_engagement_at.isoformat() if partner.last_engagement_at else None,
            },
            "nps": {
                "score": partner.nps_score,
                "reason": partner.nps_reason,
                "responded_at": partner.nps_responded_at.isoformat() if partner.nps_responded_at else None,
            },
            "support": {
                "open_tickets": partner.open_tickets,
                "avg_resolution_hours": partner.avg_resolution_hours,
            },
        }

    async def get_program_overview(self) -> dict[str, Any]:
        """Get overview stats for the design partner program."""
        all_partners = await self.repo.list_all(limit=100)

        total = len(all_partners)
        by_status = {}
        by_tier = {}

        for p in all_partners:
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
            by_tier[p.tier.value] = by_tier.get(p.tier.value, 0) + 1

        active = [p for p in all_partners if p.status == DesignPartnerStatus.ACTIVE]

        return {
            "total_partners": total,
            "by_status": by_status,
            "by_tier": by_tier,
            "active_partners": len(active),
            "avg_nps": sum(p.nps_score for p in active if p.nps_score) / len([p for p in active if p.nps_score]) if active else 0,
            "total_feedback": sum(p.feedback_count for p in all_partners),
            "total_campaigns": sum(p.campaigns_run for p in all_partners),
            "total_ai_interactions": sum(p.ai_interactions for p in all_partners),
            "partners_needing_attention": sum(1 for p in active if p.open_tickets > 5),
        }
