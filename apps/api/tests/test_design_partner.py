"""Tests for Design Partner Service — E6.1 Beta Launch."""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from app.domain.entities.design_partner import (
    DesignPartner,
    DesignPartnerFeedback,
    DesignPartnerFeedbackRepository,
    DesignPartnerRepository,
    DesignPartnerStatus,
    DesignPartnerTier,
    FeedbackPriority,
    FeedbackType,
    FeedbackStatus,
    SupportTicket,
    SupportTicketStatus,
)


class MockDesignPartnerRepo(DesignPartnerRepository):
    def __init__(self):
        self.partners: dict[uuid4, DesignPartner] = {}

    async def save(self, partner: DesignPartner) -> DesignPartner:
        self.partners[partner.id] = partner
        return partner

    async def find_by_id(self, partner_id: uuid4) -> DesignPartner | None:
        return self.partners.get(partner_id)

    async def find_by_organization(self, org_id: uuid4) -> DesignPartner | None:
        for p in self.partners.values():
            if p.organization_id == org_id:
                return p
        return None

    async def list_all(
        self,
        status: DesignPartnerStatus | None = None,
        tier: DesignPartnerTier | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DesignPartner]:
        results = list(self.partners.values())
        if status:
            results = [p for p in results if p.status == status]
        if tier:
            results = [p for p in results if p.tier == tier]
        return results[offset:offset + limit]

    async def count(self, status: DesignPartnerStatus | None = None) -> int:
        results = list(self.partners.values())
        if status:
            results = [p for p in results if p.status == status]
        return len(results)


class MockFeedbackRepo(DesignPartnerFeedbackRepository):
    def __init__(self):
        self.feedback: dict[uuid4, DesignPartnerFeedback] = {}

    async def save(self, fb: DesignPartnerFeedback) -> DesignPartnerFeedback:
        self.feedback[fb.id] = fb
        return fb

    async def find_by_id(self, feedback_id: uuid4) -> DesignPartnerFeedback | None:
        return self.feedback.get(feedback_id)

    async def find_by_partner(
        self,
        partner_id: uuid4,
        status: str | FeedbackStatus | None = None,
        type: FeedbackType | None = None,
        limit: int = 50,
    ) -> list[DesignPartnerFeedback]:
        results = [f for f in self.feedback.values() if f.design_partner_id == partner_id]
        if status:
            status_value = status.value if hasattr(status, 'value') else status
            results = [f for f in results if f.status.value == status_value]
        if type:
            results = [f for f in results if f.type == type]
        return results[:limit]

    async def list_all(
        self,
        status: str | FeedbackStatus | None = None,
        type: FeedbackType | None = None,
        priority: FeedbackPriority | None = None,
        limit: int = 50,
    ) -> list[DesignPartnerFeedback]:
        results = list(self.feedback.values())
        if status:
            status_value = status.value if hasattr(status, 'value') else status
            results = [f for f in results if f.status.value == status_value]
        if type:
            results = [f for f in results if f.type == type]
        if priority:
            results = [f for f in results if f.priority == priority]
        return results[:limit]


class MockTicketRepo:
    def __init__(self):
        self.tickets: dict[uuid4, SupportTicket] = {}

    async def save(self, ticket: SupportTicket) -> SupportTicket:
        self.tickets[ticket.id] = ticket
        return ticket

    async def find_by_id(self, ticket_id: uuid4) -> SupportTicket | None:
        return self.tickets.get(ticket_id)

    async def find_by_partner(
        self,
        partner_id: uuid4,
        status: SupportTicketStatus | None = None,
        limit: int = 50,
    ) -> list[SupportTicket]:
        results = [t for t in self.tickets.values() if t.design_partner_id == partner_id]
        if status:
            results = [t for t in results if t.status == status]
        return results[:limit]

    async def list_all(
        self,
        status: SupportTicketStatus | None = None,
        csm_id: uuid4 | None = None,
        limit: int = 50,
    ) -> list[SupportTicket]:
        results = list(self.tickets.values())
        if status:
            results = [t for t in results if t.status == status]
        if csm_id:
            results = [t for t in results if t.assigned_csm_id == csm_id]
        return results[:limit]


@pytest.fixture
def partner_repo():
    return MockDesignPartnerRepo()


@pytest.fixture
def feedback_repo():
    return MockFeedbackRepo()


@pytest.fixture
def ticket_repo():
    return MockTicketRepo()


@pytest.fixture
def service(partner_repo, feedback_repo):
    from app.domain.services.design_partner_service import DesignPartnerService
    return DesignPartnerService(partner_repo, feedback_repo)


# --- DesignPartner Entity Tests ---

class TestDesignPartner:
    def test_create_partner(self):
        org_id = uuid4()
        partner = DesignPartner(
            organization_id=org_id,
            tier=DesignPartnerTier.DESIGN_PARTNER,
        )
        assert partner.organization_id == org_id
        assert partner.tier == DesignPartnerTier.DESIGN_PARTNER
        assert partner.status == DesignPartnerStatus.PENDING
        assert partner.feedback_count == 0

    def test_start_onboarding(self):
        partner = DesignPartner(organization_id=uuid4())
        csm_id = uuid4()
        partner.start_onboarding(csm_id)

        assert partner.status == DesignPartnerStatus.ONBOARDING
        assert partner.onboarding_started_at is not None
        assert partner.onboarding_csm_id == csm_id

    def test_complete_onboarding(self):
        partner = DesignPartner(organization_id=uuid4())
        partner.status = DesignPartnerStatus.ONBOARDING
        partner.complete_onboarding()

        assert partner.status == DesignPartnerStatus.ACTIVE
        assert partner.onboarding_completed_at is not None
        assert partner.activated_at is not None

    def test_add_milestone(self):
        partner = DesignPartner(organization_id=uuid4())
        partner.add_milestone("Kickoff call completed")
        partner.add_milestone("Integration configured")

        assert len(partner.onboarding_milestones) == 2
        assert "Kickoff call completed" in partner.onboarding_milestones[0]

    def test_record_feedback(self):
        partner = DesignPartner(organization_id=uuid4())
        partner.record_feedback(FeedbackType.FEATURE_REQUEST)
        partner.record_feedback(FeedbackType.BUG_REPORT)
        partner.record_feedback(FeedbackType.FEATURE_REQUEST)

        assert partner.feedback_count == 3
        assert partner.feedback_by_type["feature_request"] == 2
        assert partner.feedback_by_type["bug_report"] == 1

    def test_update_nps(self):
        partner = DesignPartner(organization_id=uuid4())
        partner.update_nps(9)

        assert partner.nps_score == 9
        assert partner.nps_responded_at is not None

    def test_update_engagement(self):
        partner = DesignPartner(organization_id=uuid4())
        partner.update_engagement(wau=50, campaigns=5, ai_interactions=100)

        assert partner.weekly_active_users == 50
        assert partner.campaigns_run == 5
        assert partner.ai_interactions == 100
        assert partner.last_engagement_at is not None

    def test_to_dict(self):
        partner = DesignPartner(
            organization_id=uuid4(),
            tier=DesignPartnerTier.ENTERPRISE,
        )
        partner.status = DesignPartnerStatus.ACTIVE
        d = partner.to_dict()
        assert d["tier"] == "enterprise"
        assert d["status"] == "active"
        assert "id" in d


# --- DesignPartnerFeedback Entity Tests ---

class TestDesignPartnerFeedback:
    def test_create_feedback(self):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            type=FeedbackType.FEATURE_REQUEST,
            title="Add dark mode",
            description="Users want dark mode support",
        )
        assert fb.type == FeedbackType.FEATURE_REQUEST
        assert fb.priority == FeedbackPriority.MEDIUM
        assert fb.status == FeedbackStatus.OPEN

    def test_triage(self):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
        )
        assignee = uuid4()
        fb.triage(assignee)

        assert fb.status == FeedbackStatus.TRIAGED
        assert fb.assigned_to == assignee
        assert fb.triaged_at is not None

    def test_start_work(self):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
        )
        fb.start_work()
        assert fb.status == FeedbackStatus.IN_PROGRESS

    def test_resolve(self):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
        )
        fb.resolve("Implemented dark mode toggle in settings")

        assert fb.status == FeedbackStatus.RESOLVED
        assert fb.resolution_notes == "Implemented dark mode toggle in settings"
        assert fb.resolved_at is not None

    def test_close(self):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
        )
        fb.status = FeedbackStatus.RESOLVED
        fb.close()
        assert fb.status == FeedbackStatus.CLOSED


# --- SupportTicket Entity Tests ---

class TestSupportTicket:
    def test_create_ticket(self):
        ticket = SupportTicket(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            subject="Cannot connect Meta Ads",
            priority=FeedbackPriority.HIGH,
        )
        assert ticket.status == SupportTicketStatus.OPEN
        assert ticket.priority == FeedbackPriority.HIGH

    def test_sla_breach_check(self):
        ticket = SupportTicket(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            resolution_due_at=datetime.now(UTC) - timedelta(hours=1),  # Overdue
        )
        ticket.status = SupportTicketStatus.IN_PROGRESS
        assert ticket.is_sla_breached() is True

    def test_sla_not_breached_if_resolved(self):
        ticket = SupportTicket(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            resolution_due_at=datetime.now(UTC) - timedelta(hours=1),
        )
        ticket.status = SupportTicketStatus.RESOLVED
        assert ticket.is_sla_breached() is False

    def test_hours_to_first_response(self):
        ticket = SupportTicket(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
        )
        ticket.first_responded_at = ticket.created_at + timedelta(hours=2)
        hours = ticket.hours_to_first_response()
        assert hours is not None
        assert 1.9 < hours < 2.1


# --- DesignPartnerService Tests ---

class TestDesignPartnerService:
    @pytest.mark.asyncio
    async def test_create_partner(self, service):
        org_id = uuid4()
        partner = await service.create_partner(
            organization_id=org_id,
            tier=DesignPartnerTier.DESIGN_PARTNER,
            support_tier="priority",
        )
        assert partner.organization_id == org_id
        assert partner.tier == DesignPartnerTier.DESIGN_PARTNER
        assert partner.status == DesignPartnerStatus.PENDING

    @pytest.mark.asyncio
    async def test_approve_partner(self, service, partner_repo):
        partner = await service.create_partner(uuid4())
        approved = await service.approve_partner(partner.id, uuid4())

        assert approved.status == DesignPartnerStatus.APPROVED
        assert approved.approved_at is not None
        assert approved.contract_signed_at is not None

    @pytest.mark.asyncio
    async def test_start_onboarding(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())

        csm_id = uuid4()
        onboarded = await service.start_onboarding(partner.id, csm_id)

        assert onboarded.status == DesignPartnerStatus.ONBOARDING
        assert onboarded.onboarding_started_at is not None
        assert onboarded.onboarding_csm_id == csm_id

    @pytest.mark.asyncio
    async def test_complete_onboarding(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        csm_id = uuid4()
        await service.start_onboarding(partner.id, csm_id)

        completed = await service.complete_onboarding(partner.id)

        assert completed.status == DesignPartnerStatus.ACTIVE
        assert completed.onboarding_completed_at is not None
        assert completed.activated_at is not None

    @pytest.mark.asyncio
    async def test_add_milestone(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())

        await service.add_milestone(partner.id, "Kickoff call done")

        updated = await service.get_partner(partner.id)
        assert "Kickoff call done" in updated.onboarding_milestones[0]

    @pytest.mark.asyncio
    async def test_list_partners(self, service):
        for _ in range(3):
            p = await service.create_partner(uuid4())
            await service.approve_partner(p.id, uuid4())
            await service.start_onboarding(p.id, uuid4())
            await service.complete_onboarding(p.id)

        active = await service.list_partners(status=DesignPartnerStatus.ACTIVE)
        assert len(active) == 3

        pending = await service.list_partners(status=DesignPartnerStatus.PENDING)
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_submit_feedback(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())
        await service.complete_onboarding(partner.id)

        user_id = uuid4()
        fb = await service.submit_feedback(
            partner_id=partner.id,
            organization_id=org_id,
            user_id=user_id,
            feedback_type=FeedbackType.FEATURE_REQUEST,
            title="Add dark mode",
            description="Users are requesting dark mode support",
            priority=FeedbackPriority.HIGH,
            feature_area="UI/UX",
        )

        assert fb.type == FeedbackType.FEATURE_REQUEST
        assert fb.priority == FeedbackPriority.HIGH
        assert fb.feature_area == "UI/UX"

        # Check partner stats updated
        updated = await service.get_partner(partner.id)
        assert updated.feedback_count == 1
        assert updated.feedback_by_type["feature_request"] == 1

    @pytest.mark.asyncio
    async def test_submit_nps_feedback(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())
        await service.complete_onboarding(partner.id)

        fb = await service.submit_feedback(
            partner_id=partner.id,
            organization_id=org_id,
            user_id=uuid4(),
            feedback_type=FeedbackType.NPS_SURVEY,
            title="NPS Survey",
            description="Quarterly NPS",
            nps_score=9,
            nps_reason="Love the AI content generation",
        )

        assert fb.nps_score == 9
        assert fb.nps_reason == "Love the AI content generation"

        updated = await service.get_partner(partner.id)
        assert updated.nps_score == 9

    @pytest.mark.asyncio
    async def test_feedback_triage_and_resolution(self, service, feedback_repo):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())
        await service.complete_onboarding(partner.id)

        fb = await service.submit_feedback(
            partner_id=partner.id,
            organization_id=org_id,
            user_id=uuid4(),
            feedback_type=FeedbackType.BUG_REPORT,
            title="Campaign creation fails",
            description="Error when creating campaign with special characters",
        )

        # Triaged
        fb.triage(uuid4())
        await feedback_repo.save(fb)

        assert fb.status.value == "triaged"

        # Resolved
        fb.resolve("Fixed special character escaping")
        await feedback_repo.save(fb)

        assert fb.status == "resolved"
        assert fb.resolved_at is not None
        assert fb.resolution_notes == "Fixed special character escaping"

    @pytest.mark.asyncio
    async def test_record_engagement(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())
        await service.complete_onboarding(partner.id)

        updated = await service.record_engagement(
            partner.id, wau=100, campaigns=10, ai_interactions=500
        )

        assert updated.weekly_active_users == 100
        assert updated.campaigns_run == 10
        assert updated.ai_interactions == 500
        assert updated.last_engagement_at is not None

    @pytest.mark.asyncio
    async def test_update_nps(self, service):
        org_id = uuid4()
        partner = await service.create_partner(org_id)
        await service.approve_partner(partner.id, uuid4())
        await service.start_onboarding(partner.id, uuid4())
        await service.complete_onboarding(partner.id)

        updated = await service.update_nps(partner.id, 10)
        assert updated.nps_score == 10


# --- Feedback Repository Tests ---

class TestFeedbackRepository:
    @pytest.mark.asyncio
    async def test_save_and_find(self, feedback_repo):
        fb = DesignPartnerFeedback(
            design_partner_id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            type=FeedbackType.FEATURE_REQUEST,
            title="Test",
            description="Test description",
        )
        saved = await feedback_repo.save(fb)
        found = await feedback_repo.find_by_id(saved.id)
        assert found is not None
        assert found.title == "Test"

    @pytest.mark.asyncio
    async def test_find_by_partner(self, feedback_repo):
        partner_id = uuid4()
        fb1 = DesignPartnerFeedback(
            design_partner_id=partner_id, organization_id=uuid4(), user_id=uuid4(),
            type=FeedbackType.FEATURE_REQUEST, title="A", description="A"
        )
        fb2 = DesignPartnerFeedback(
            design_partner_id=partner_id, organization_id=uuid4(), user_id=uuid4(),
            type=FeedbackType.BUG_REPORT, title="B", description="B"
        )
        fb3 = DesignPartnerFeedback(
            design_partner_id=uuid4(), organization_id=uuid4(), user_id=uuid4(),
            type=FeedbackType.FEATURE_REQUEST, title="C", description="C"
        )
        await feedback_repo.save(fb1)
        await feedback_repo.save(fb2)
        await feedback_repo.save(fb3)

        results = await feedback_repo.find_by_partner(partner_id)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_by_partner_filtered(self, feedback_repo):
        partner_id = uuid4()
        fb1 = DesignPartnerFeedback(
            design_partner_id=partner_id, organization_id=uuid4(), user_id=uuid4(),
            type=FeedbackType.FEATURE_REQUEST, status=FeedbackStatus.RESOLVED, title="A", description="A"
        )
        fb2 = DesignPartnerFeedback(
            design_partner_id=partner_id, organization_id=uuid4(), user_id=uuid4(),
            type=FeedbackType.BUG_REPORT, status=FeedbackStatus.OPEN, title="B", description="B"
        )
        await feedback_repo.save(fb1)
        await feedback_repo.save(fb2)

        resolved = await feedback_repo.find_by_partner(partner_id, status="resolved")
        assert len(resolved) == 1
        assert resolved[0].title == "A"

        open_fb = await feedback_repo.find_by_partner(partner_id, status="open")
        assert len(open_fb) == 1
        assert open_fb[0].title == "B"


# --- DesignPartnerRepository Tests ---

class TestDesignPartnerRepository:
    @pytest.mark.asyncio
    async def test_save_and_find(self, partner_repo):
        partner = DesignPartner(organization_id=uuid4())
        saved = await partner_repo.save(partner)
        found = await partner_repo.find_by_id(saved.id)
        assert found is not None
        assert found.organization_id == partner.organization_id

    @pytest.mark.asyncio
    async def test_find_by_organization(self, partner_repo):
        org_id = uuid4()
        partner = DesignPartner(organization_id=org_id)
        await partner_repo.save(partner)

        found = await partner_repo.find_by_organization(org_id)
        assert found is not None
        assert found.organization_id == org_id

    @pytest.mark.asyncio
    async def test_list_all(self, partner_repo):
        for i in range(5):
            p = DesignPartner(organization_id=uuid4())
            p.status = DesignPartnerStatus.ACTIVE if i < 3 else DesignPartnerStatus.PENDING
            await partner_repo.save(p)

        active = await partner_repo.list_all(status=DesignPartnerStatus.ACTIVE)
        assert len(active) == 3

        pending = await partner_repo.list_all(status=DesignPartnerStatus.PENDING)
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_count(self, partner_repo):
        for i in range(4):
            p = DesignPartner(organization_id=uuid4())
            p.status = DesignPartnerStatus.ACTIVE if i < 3 else DesignPartnerStatus.PENDING
            await partner_repo.save(p)

        total = await partner_repo.count()
        active = await partner_repo.count(DesignPartnerStatus.ACTIVE)
        pending = await partner_repo.count(DesignPartnerStatus.PENDING)

        assert total == 4
        assert active == 3
        assert pending == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])