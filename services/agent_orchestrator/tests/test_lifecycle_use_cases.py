"""Tests for Campaign Lifecycle Use Cases — launch, pause, resume, complete, archive.

All tests are pure unit tests with a mock repository — no DB required.
"""

from datetime import date
from uuid import uuid4

import pytest
from app.application.use_cases.campaigns.lifecycle_use_cases import (
    ArchiveCampaignUseCase,
    CompleteCampaignUseCase,
    LaunchCampaignUseCase,
    PauseCampaignUseCase,
    ResumeCampaignUseCase,
)
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.exceptions.domain_exceptions import ValidationError

# ── Helpers ──────────────────────────────────────────────────────────


class MockCampaignRepo:
    def __init__(self, campaign: Campaign):
        self._campaign = campaign
        self.saved = False

    async def save(self, campaign):
        self._campaign = campaign
        self.saved = True
        return campaign

    async def find_by_id(self, campaign_id):
        return self._campaign


def _make_campaign(status: str = "draft", channels: list[str] | None = None) -> Campaign:
    c = Campaign.create(
        organization_id=uuid4(),
        name="Test Campaign",
        created_by=uuid4(),
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        channels=channels or [],
    )
    c.status = status
    c.budget_amount = 10000.0
    return c


# ── Launch Tests ─────────────────────────────────────────────────────


class TestLaunchCampaign:
    def test_launch_draft(self):
        """Draft → active succeeds."""
        campaign = _make_campaign(status="draft")
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "active"
        assert repo.saved is True

    def test_launch_pending_approval(self):
        """pending_approval → active succeeds."""
        campaign = _make_campaign(status="pending_approval")
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "active"

    def test_launch_active_fails(self):
        """Active campaign cannot be launched."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot launch"):
            asyncio.run(uc.execute(campaign.id))

    def test_launch_paused_fails(self):
        """Paused campaign cannot be launched."""
        campaign = _make_campaign(status="paused")
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot launch"):
            asyncio.run(uc.execute(campaign.id))

    def test_launch_no_start_date_fails(self):
        """Missing start_date → ValidationError."""
        campaign = _make_campaign(status="draft")
        campaign.start_date = None
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="start_date"):
            asyncio.run(uc.execute(campaign.id))

    def test_launch_ads_without_budget_fails(self):
        """Ads channel + no budget → ValidationError."""
        campaign = _make_campaign(status="draft", channels=["ads"])
        campaign.budget_amount = None
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="budget"):
            asyncio.run(uc.execute(campaign.id))

    def test_launch_ads_with_budget_succeeds(self):
        """Ads channel + budget → succeeds."""
        campaign = _make_campaign(status="draft", channels=["ads"])
        campaign.budget_amount = 5000.0
        repo = MockCampaignRepo(campaign)
        uc = LaunchCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "active"


# ── Pause Tests ──────────────────────────────────────────────────────


class TestPauseCampaign:
    def test_pause_active(self):
        """Active → paused succeeds."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = PauseCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "paused"

    def test_pause_draft_fails(self):
        """Draft cannot be paused."""
        campaign = _make_campaign(status="draft")
        repo = MockCampaignRepo(campaign)
        uc = PauseCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot pause"):
            asyncio.run(uc.execute(campaign.id))

    def test_pause_paused_fails(self):
        """Already paused → ValidationError."""
        campaign = _make_campaign(status="paused")
        repo = MockCampaignRepo(campaign)
        uc = PauseCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot pause"):
            asyncio.run(uc.execute(campaign.id))

    def test_pause_with_reason(self):
        """Pause with a reason."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = PauseCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id, reason="Budget concern"))

        assert result.status == "paused"


# ── Resume Tests ─────────────────────────────────────────────────────


class TestResumeCampaign:
    def test_resume_paused(self):
        """Paused → active succeeds."""
        campaign = _make_campaign(status="paused")
        repo = MockCampaignRepo(campaign)
        uc = ResumeCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "active"

    def test_resume_active_fails(self):
        """Active cannot be resumed."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = ResumeCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot resume"):
            asyncio.run(uc.execute(campaign.id))

    def test_resume_draft_fails(self):
        """Draft cannot be resumed."""
        campaign = _make_campaign(status="draft")
        repo = MockCampaignRepo(campaign)
        uc = ResumeCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot resume"):
            asyncio.run(uc.execute(campaign.id))


# ── Complete Tests ───────────────────────────────────────────────────


class TestCompleteCampaign:
    def test_complete_active(self):
        """Active → completed succeeds."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = CompleteCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "completed"

    def test_complete_paused(self):
        """Paused → completed succeeds."""
        campaign = _make_campaign(status="paused")
        repo = MockCampaignRepo(campaign)
        uc = CompleteCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "completed"

    def test_complete_draft_fails(self):
        """Draft cannot be completed."""
        campaign = _make_campaign(status="draft")
        repo = MockCampaignRepo(campaign)
        uc = CompleteCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot complete"):
            asyncio.run(uc.execute(campaign.id))

    def test_complete_already_completed_fails(self):
        """Completed → Completed is not valid."""
        campaign = _make_campaign(status="completed")
        repo = MockCampaignRepo(campaign)
        uc = CompleteCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot complete"):
            asyncio.run(uc.execute(campaign.id))


# ── Archive Tests ────────────────────────────────────────────────────


class TestArchiveCampaign:
    def test_archive_completed(self):
        """Completed → archived succeeds."""
        campaign = _make_campaign(status="completed")
        repo = MockCampaignRepo(campaign)
        uc = ArchiveCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "archived"

    def test_archive_already_archived_fails(self):
        """Already archived → ValidationError."""
        campaign = _make_campaign(status="archived")
        repo = MockCampaignRepo(campaign)
        uc = ArchiveCampaignUseCase(repo)

        with pytest.raises(ValidationError, match="already archived"):
            asyncio.run(uc.execute(campaign.id))

    def test_archive_active_succeeds(self):
        """Active → archived is a valid transition."""
        campaign = _make_campaign(status="active")
        repo = MockCampaignRepo(campaign)
        uc = ArchiveCampaignUseCase(repo)

        result = asyncio.run(uc.execute(campaign.id))

        assert result.status == "archived"


# ── Need asyncio import ─────────────────────────────────────────────
import asyncio
