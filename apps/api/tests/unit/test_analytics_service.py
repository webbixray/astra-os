from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.analytics.analytics_service import AnalyticsService


@pytest.fixture
def campaign_repo():
    return MagicMock()


@pytest.fixture
def content_repo():
    return MagicMock()


@pytest.fixture
def service(campaign_repo, content_repo):
    return AnalyticsService(campaign_repo=campaign_repo, content_repo=content_repo)


def make_campaign(status: str = "active", budget: float = 1000.0, name: str = "Campaign"):
    c = MagicMock()
    c.id = uuid4()
    c.name = name
    c.status = status
    c.budget_amount = budget
    c.channels = ["social"]
    return c


def make_content(status: str = "published"):
    c = MagicMock()
    c.id = uuid4()
    c.status = status
    return c


class TestGetOverview:
    async def test_empty(self, service, campaign_repo, content_repo):
        campaign_repo.find_by_organization = AsyncMock(return_value=[])
        content_repo.find_by_organization = AsyncMock(return_value=[])

        result = await service.get_overview(uuid4())

        assert result["total_campaigns"] == 0
        assert result["total_content"] == 0
        assert result["total_budget"] == 0

    async def test_with_data(self, service, campaign_repo, content_repo):
        campaigns = [
            make_campaign(status="active", budget=5000),
            make_campaign(status="active", budget=3000),
            make_campaign(status="draft", budget=1000),
            make_campaign(status="completed", budget=2000),
        ]
        contents = [
            make_content(status="published"),
            make_content(status="draft"),
            make_content(status="published"),
        ]
        campaign_repo.find_by_organization = AsyncMock(return_value=campaigns)
        content_repo.find_by_organization = AsyncMock(return_value=contents)

        result = await service.get_overview(uuid4())

        assert result["total_campaigns"] == 4
        assert result["active_campaigns"] == 2
        assert result["draft_campaigns"] == 1
        assert result["completed_campaigns"] == 1
        assert result["total_content"] == 3
        assert result["published_content"] == 2
        assert result["total_budget"] == 11000
        assert result["status_breakdown"] == {"active": 2, "draft": 1, "completed": 1}

    async def test_zero_budget(self, service, campaign_repo, content_repo):
        campaigns = [make_campaign(status="active", budget=None)]
        campaign_repo.find_by_organization = AsyncMock(return_value=campaigns)
        content_repo.find_by_organization = AsyncMock(return_value=[])

        result = await service.get_overview(uuid4())

        assert result["total_budget"] == 0


class TestGetCampaignPerformance:
    async def test_empty(self, service, campaign_repo):
        campaign_repo.find_by_organization = AsyncMock(return_value=[])

        result = await service.get_campaign_performance(uuid4())

        assert result == []

    async def test_with_data(self, service, campaign_repo):
        c = make_campaign(name="Test Campaign", budget=5000)
        campaign_repo.find_by_organization = AsyncMock(return_value=[c])

        result = await service.get_campaign_performance(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Test Campaign"
        assert result[0]["budget"] == 5000
        assert result[0]["spend"] == 0

    async def test_zero_budget(self, service, campaign_repo):
        c = make_campaign(budget=None)
        campaign_repo.find_by_organization = AsyncMock(return_value=[c])

        result = await service.get_campaign_performance(uuid4())

        assert result[0]["budget"] == 0


class TestGetAdPerformance:
    async def test_empty(self, service):
        result = await service.get_ad_performance([])

        assert result["total_impressions"] == 0
        assert result["total_clicks"] == 0
        assert result["ctr"] == 0
        assert result["platforms"] == []

    async def test_with_data(self, service):
        mock_campaigns = [
            MagicMock(impressions=1000, clicks=50, spend=100, conversions=5, revenue=500, budget=1000,
                      platform=MagicMock(value="google"), id="c1", name="Campaign 1"),
            MagicMock(impressions=2000, clicks=100, spend=200, conversions=10, revenue=1000, budget=2000,
                      platform=MagicMock(value="google"), id="c2", name="Campaign 2"),
        ]

        with patch("app.application.use_cases.analytics.analytics_service.AdPlatformFactory") as mock_factory:
            mock_factory.get_connected_campaigns = AsyncMock(return_value=mock_campaigns)
            result = await service.get_ad_performance([{"platform": "google", "access_token": "tok"}])

        assert result["total_impressions"] == 3000
        assert result["total_clicks"] == 150
        assert result["total_spend"] == 300
        assert result["ctr"] == 5.0
        assert result["cpc"] == 2.0
        assert len(result["platforms"]) == 1
        assert result["platforms"][0]["name"] == "google"
