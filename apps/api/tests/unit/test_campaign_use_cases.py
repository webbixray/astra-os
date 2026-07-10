from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.use_cases.campaigns.campaign_use_cases import (
    CreateCampaignUseCase,
    GetCampaignUseCase,
    ListCampaignsUseCase,
    UpdateCampaignUseCase,
)
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


@pytest.fixture
def repo():
    r = AsyncMock()
    r.save = AsyncMock()
    r.find_by_id = AsyncMock()
    r.find_by_organization = AsyncMock()
    return r


class TestCreateCampaignUseCase:
    @pytest.fixture(autouse=True)
    def _setup(self, repo):
        repo.save.side_effect = lambda c: c

    @pytest.fixture
    def use_case(self, repo):
        return CreateCampaignUseCase(repo=repo)

    async def test_create(self, use_case, repo):
        org_id = uuid4()
        user_id = uuid4()

        result = await use_case.execute(
            organization_id=org_id,
            name="Test Campaign",
            created_by=user_id,
            description="A test",
            budget_amount=5000.0,
        )

        assert result.name == "Test Campaign"
        repo.save.assert_awaited_once()

    async def test_create_with_dates(self, use_case, repo):
        org_id = uuid4()
        user_id = uuid4()

        result = await use_case.execute(
            organization_id=org_id,
            name="Scheduled Campaign",
            created_by=user_id,
            start_date="2025-01-01",
            end_date="2025-12-31",
            channels=["social", "email"],
            objective="awareness",
        )

        assert result.name == "Scheduled Campaign"
        assert result.start_date is not None
        assert result.end_date is not None

    async def test_create_without_optional_fields(self, use_case, repo):
        org_id = uuid4()
        user_id = uuid4()

        result = await use_case.execute(
            organization_id=org_id,
            name="Minimal Campaign",
            created_by=user_id,
        )

        assert result.name == "Minimal Campaign"
        assert result.description is None


class TestGetCampaignUseCase:
    @pytest.fixture
    def use_case(self, repo):
        return GetCampaignUseCase(repo=repo)

    async def test_get_existing(self, use_case, repo):
        campaign_id = uuid4()
        org_id = uuid4()
        campaign = Campaign.create(
            organization_id=org_id, name="Found", created_by=uuid4(),
        )
        campaign.id = campaign_id
        repo.find_by_id.return_value = campaign

        result = await use_case.execute(campaign_id=campaign_id)

        assert result.id == campaign_id
        assert result.name == "Found"

    async def test_get_nonexistent(self, use_case, repo):
        repo.find_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(campaign_id=uuid4())


class TestListCampaignsUseCase:
    @pytest.fixture
    def use_case(self, repo):
        return ListCampaignsUseCase(repo=repo)

    async def test_list_all(self, use_case, repo):
        org_id = uuid4()
        campaigns = [
            Campaign.create(organization_id=org_id, name="A", created_by=uuid4()),
            Campaign.create(organization_id=org_id, name="B", created_by=uuid4()),
        ]
        repo.find_by_organization.return_value = campaigns

        result = await use_case.execute(org_id=org_id)

        assert len(result) == 2
        assert result[0].name == "A"

    async def test_list_empty(self, use_case, repo):
        repo.find_by_organization.return_value = []

        result = await use_case.execute(org_id=uuid4())

        assert result == []

    async def test_list_filter_by_status(self, use_case, repo):
        org_id = uuid4()
        repo.find_by_organization.return_value = []

        _ = await use_case.execute(org_id=org_id, status="active")

        repo.find_by_organization.assert_awaited_with(org_id, status="active")


class TestUpdateCampaignUseCase:
    @pytest.fixture(autouse=True)
    def _setup(self, repo):
        repo.save.side_effect = lambda c: c

    @pytest.fixture
    def use_case(self, repo):
        return UpdateCampaignUseCase(repo=repo)

    async def test_update_fields(self, use_case, repo):
        campaign_id = uuid4()
        campaign = Campaign.create(
            organization_id=uuid4(), name="Original", created_by=uuid4(),
        )
        campaign.id = campaign_id
        repo.find_by_id.return_value = campaign

        result = await use_case.execute(
            campaign_id=campaign_id,
            name="Updated",
            description="New desc",
            budget_amount=9999.0,
        )

        assert result.name == "Updated"
        assert result.description == "New desc"
        assert result.budget_amount == 9999.0

    async def test_update_status_transition(self, use_case, repo):
        campaign_id = uuid4()
        campaign = Campaign.create(
            organization_id=uuid4(), name="Status Test", created_by=uuid4(),
        )
        campaign.id = campaign_id
        repo.find_by_id.return_value = campaign

        result = await use_case.execute(
            campaign_id=campaign_id,
            status="pending_approval",
        )

        assert result.status == "pending_approval"

    async def test_update_nonexistent(self, use_case, repo):
        repo.find_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(campaign_id=uuid4(), name="Nope")
