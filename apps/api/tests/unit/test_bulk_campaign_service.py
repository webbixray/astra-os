from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.calendar.bulk_campaign_service import BulkCampaignService


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def service(session):
    return BulkCampaignService(session=session)


def make_campaign_model(status: str = "active", platform: str | None = None):
    c = MagicMock()
    c.status = status
    c.platform = platform
    return c


class TestUpdateStatus:
    async def test_update_status_campaign_scope(self, service, session):
        result_mock = MagicMock()
        result_mock.rowcount = 5
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()

        result = await service.update_status(uuid4(), [uuid4(), uuid4()], "paused")

        assert result["updated"] == 5
        assert result["status"] == "paused"
        assert result["scope"] == "campaign"

    async def test_update_status_ad_scope(self, service, session):
        result_mock = MagicMock()
        result_mock.rowcount = 3
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()

        result = await service.update_status(uuid4(), [uuid4()], "active", scope="ad")

        assert result["updated"] == 3
        assert result["scope"] == "ad"

    async def test_update_status_no_rows(self, service, session):
        result_mock = MagicMock()
        result_mock.rowcount = 0
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()

        result = await service.update_status(uuid4(), [uuid4()], "archived")

        assert result["updated"] == 0


class TestGetOverview:
    async def test_get_overview_empty(self, service, session):
        campaign_result = MagicMock()
        campaign_result.scalars.return_value.all.return_value = []
        ad_result = MagicMock()
        ad_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(side_effect=[campaign_result, ad_result])

        result = await service.get_overview(uuid4())

        assert result["total_campaigns"] == 0
        assert result["total_ad_campaigns"] == 0
        assert result["combined_total"] == 0

    async def test_get_overview_with_data(self, service, session):
        campaigns = [
            make_campaign_model(status="active"),
            make_campaign_model(status="active"),
            make_campaign_model(status="paused"),
        ]
        ad_campaigns = [
            make_campaign_model(status="active", platform="google"),
            make_campaign_model(status="active", platform="meta"),
            make_campaign_model(status="paused", platform="google"),
        ]
        campaign_result = MagicMock()
        campaign_result.scalars.return_value.all.return_value = campaigns
        ad_result = MagicMock()
        ad_result.scalars.return_value.all.return_value = ad_campaigns
        session.execute = AsyncMock(side_effect=[campaign_result, ad_result])

        result = await service.get_overview(uuid4())

        assert result["total_campaigns"] == 3
        assert result["total_ad_campaigns"] == 3
        assert result["combined_total"] == 6
        assert result["campaign_status_breakdown"] == {"active": 2, "paused": 1}
        assert result["ad_campaign_status_breakdown"] == {"active": 2, "paused": 1}
        assert result["ad_platform_breakdown"] == {"google": 2, "meta": 1}

    async def test_get_overview_missing_platform(self, service, session):
        ad_campaigns = [
            make_campaign_model(status="active", platform=None),
        ]
        campaign_result = MagicMock()
        campaign_result.scalars.return_value.all.return_value = []
        ad_result = MagicMock()
        ad_result.scalars.return_value.all.return_value = ad_campaigns
        session.execute = AsyncMock(side_effect=[campaign_result, ad_result])

        result = await service.get_overview(uuid4())

        assert result["ad_platform_breakdown"] == {"unknown": 1}
