from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.entities.adplatforms.platform import AdCampaign, AdPlatform, AdStatus
from app.infrastructure.external_adapters.adplatforms.base_adapter import (
    MOCK_GOOGLE_CAMPAIGNS,
    MOCK_META_CAMPAIGNS,
    AdPlatformFactory,
    BaseAdAdapter,
    GoogleAdsAdapter,
    LinkedInAdsAdapter,
    MetaAdsAdapter,
    TikTokAdsAdapter,
    _is_mock_mode,
)


class TestIsMockMode:
    def test_none_credentials_is_mock(self):
        assert _is_mock_mode(None) is True

    def test_empty_dict_is_mock(self):
        assert _is_mock_mode({}) is True

    def test_all_empty_values_is_mock(self):
        assert _is_mock_mode({"token": "", "secret": None}) is True

    def test_has_value_is_not_mock(self):
        assert _is_mock_mode({"token": "abc123"}) is False


class TestBaseAdAdapter:
    @pytest.fixture
    def adapter(self):
        class ConcreteAdapter(BaseAdAdapter):
            platform = AdPlatform.GOOGLE_ADS
            async def get_campaigns(self, account_id): return []
            async def get_performance(self, account_id, campaign_ids=None): return []
            async def create_campaign(self, campaign): return ""
            async def update_campaign_status(self, campaign_id, status): return True
        return ConcreteAdapter()

    @pytest.mark.asyncio
    async def test_get_client_lazily_creates(self, adapter):
        client = await adapter.get_client()
        assert client is not None

    @pytest.mark.asyncio
    async def test_get_client_is_cached(self, adapter):
        c1 = await adapter.get_client()
        c2 = await adapter.get_client()
        assert c1 is c2

    @pytest.mark.asyncio
    async def test_close_resets_client(self, adapter):
        await adapter.get_client()
        await adapter.close()
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_close_on_none_client(self, adapter):
        await adapter.close()
        assert adapter._client is None

    def test_map_status_google_enabled(self, adapter):
        result = adapter._map_status("ENABLED", AdPlatform.GOOGLE_ADS)
        assert result == AdStatus.ACTIVE

    def test_map_status_google_paused(self, adapter):
        result = adapter._map_status("PAUSED", AdPlatform.GOOGLE_ADS)
        assert result == AdStatus.PAUSED

    def test_map_status_google_removed(self, adapter):
        result = adapter._map_status("REMOVED", AdPlatform.GOOGLE_ADS)
        assert result == AdStatus.COMPLETED

    def test_map_status_meta_active(self, adapter):
        result = adapter._map_status("ACTIVE", AdPlatform.META)
        assert result == AdStatus.ACTIVE

    def test_map_status_unknown_defaults_active(self, adapter):
        result = adapter._map_status("UNKNOWN", AdPlatform.GOOGLE_ADS)
        assert result == AdStatus.ACTIVE


class TestGoogleAdsAdapter:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_mock_campaigns(self):
        adapter = GoogleAdsAdapter()
        campaigns = await adapter.get_campaigns("account-1")
        assert campaigns == MOCK_GOOGLE_CAMPAIGNS
        assert len(campaigns) == 2

    @pytest.mark.asyncio
    async def test_real_mode_parses_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "results": [
                {
                    "campaign": {"id": "101", "name": "Real Campaign", "status": "ENABLED"},
                    "metrics": {
                        "impressions": 1000, "clicks": 50,
                        "conversions": 5, "costMicros": 2000000,
                    },
                }
            ]
        })

        with patch.object(GoogleAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = GoogleAdsAdapter(credentials={"access_token": "tok", "developer_token": "dev", "customer_id": "123"})
            campaigns = await adapter.get_campaigns("customer-123")

        assert len(campaigns) == 1
        assert campaigns[0].id == "101"
        assert campaigns[0].name == "Real Campaign"
        assert campaigns[0].status == AdStatus.ACTIVE
        assert campaigns[0].spend == 2.0
        assert campaigns[0].impressions == 1000

    @pytest.mark.asyncio
    async def test_http_error_falls_back_to_mock(self):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch.object(GoogleAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = GoogleAdsAdapter(credentials={"access_token": "tok", "developer_token": "dev"})
            campaigns = await adapter.get_campaigns("customer-123")

        assert campaigns == MOCK_GOOGLE_CAMPAIGNS

    @pytest.mark.asyncio
    async def test_get_performance_calls_get_campaigns(self):
        adapter = GoogleAdsAdapter()
        campaigns = await adapter.get_performance("account-1")
        assert campaigns == MOCK_GOOGLE_CAMPAIGNS

    @pytest.mark.asyncio
    async def test_create_campaign_mock_returns_fixed_id(self):
        adapter = GoogleAdsAdapter()
        result = await adapter.create_campaign(AdCampaign(name="Test"))
        assert result == "google-new-campaign-id"

    @pytest.mark.asyncio
    async def test_update_campaign_status_returns_true(self):
        adapter = GoogleAdsAdapter()
        result = await adapter.update_campaign_status("camp-1", "PAUSED")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_campaign_real_mode(self):
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={"id": "real-123"})

        with patch.object(GoogleAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = GoogleAdsAdapter(credentials={"access_token": "tok", "developer_token": "dev", "customer_id": "c-1"})
            result = await adapter.create_campaign(AdCampaign(name="New"))
            assert result == "real-123"


class TestMetaAdsAdapter:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_mock_campaigns(self):
        adapter = MetaAdsAdapter()
        campaigns = await adapter.get_campaigns("act_123")
        assert campaigns == MOCK_META_CAMPAIGNS
        assert len(campaigns) == 1

    @pytest.mark.asyncio
    async def test_real_mode_parses_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "data": [
                {
                    "id": "m-1", "name": "Meta Campaign", "status": "ACTIVE",
                    "daily_budget": 5000,
                    "insights": {"data": [{"impressions": 500, "clicks": 20, "conversions": 2, "spend": 150.0}]},
                }
            ]
        })

        with patch.object(MetaAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = MetaAdsAdapter(credentials={"access_token": "tok"})
            campaigns = await adapter.get_campaigns("act_123")

        assert len(campaigns) == 1
        assert campaigns[0].id == "m-1"
        assert campaigns[0].name == "Meta Campaign"
        assert campaigns[0].status == AdStatus.ACTIVE
        assert campaigns[0].spend == 150.0

    @pytest.mark.asyncio
    async def test_http_error_falls_back_to_mock(self):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(MetaAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = MetaAdsAdapter(credentials={"access_token": "tok"})
            campaigns = await adapter.get_campaigns("act_456")

        assert campaigns == MOCK_META_CAMPAIGNS

    @pytest.mark.asyncio
    async def test_create_campaign_returns_fixed_id(self):
        adapter = MetaAdsAdapter()
        result = await adapter.create_campaign(AdCampaign(name="M"))
        assert result == "meta-new-campaign-id"

    @pytest.mark.asyncio
    async def test_update_campaign_status_returns_true(self):
        adapter = MetaAdsAdapter()
        result = await adapter.update_campaign_status("c-1", "PAUSED")
        assert result is True


class TestLinkedInAdsAdapter:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_empty(self):
        adapter = LinkedInAdsAdapter()
        campaigns = await adapter.get_campaigns("account-1")
        assert campaigns == []

    @pytest.mark.asyncio
    async def test_real_mode_parses_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "elements": [{"id": "li-1", "name": "LinkedIn Campaign"}]
        })

        with patch.object(LinkedInAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = LinkedInAdsAdapter(credentials={"access_token": "tok"})
            campaigns = await adapter.get_campaigns("account-1")

        assert len(campaigns) == 1
        assert campaigns[0].id == "li-1"
        assert campaigns[0].name == "LinkedIn Campaign"

    @pytest.mark.asyncio
    async def test_http_error_returns_empty(self):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch.object(LinkedInAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = LinkedInAdsAdapter(credentials={"access_token": "tok"})
            campaigns = await adapter.get_campaigns("account-1")

        assert campaigns == []


class TestTikTokAdsAdapter:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_empty(self):
        adapter = TikTokAdsAdapter()
        campaigns = await adapter.get_campaigns("advertiser-1")
        assert campaigns == []

    @pytest.mark.asyncio
    async def test_real_mode_parses_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "data": {"list": [{"campaign_id": "tt-1", "campaign_name": "TikTok Campaign"}]}
        })

        with patch.object(TikTokAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = TikTokAdsAdapter(credentials={"access_token": "tok", "advertiser_id": "adv-1"})
            campaigns = await adapter.get_campaigns("adv-1")

        assert len(campaigns) == 1
        assert campaigns[0].id == "tt-1"
        assert campaigns[0].name == "TikTok Campaign"

    @pytest.mark.asyncio
    async def test_http_error_returns_empty(self):
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch.object(TikTokAdsAdapter, "get_client", new=AsyncMock()) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            adapter = TikTokAdsAdapter(credentials={"access_token": "tok"})
            campaigns = await adapter.get_campaigns("adv-1")

        assert campaigns == []


class TestAdPlatformFactory:
    def test_create_google_ads(self):
        adapter = AdPlatformFactory.create(AdPlatform.GOOGLE_ADS)
        assert isinstance(adapter, GoogleAdsAdapter)

    def test_create_meta(self):
        adapter = AdPlatformFactory.create(AdPlatform.META)
        assert isinstance(adapter, MetaAdsAdapter)

    def test_create_linkedin(self):
        adapter = AdPlatformFactory.create(AdPlatform.LINKEDIN)
        assert isinstance(adapter, LinkedInAdsAdapter)

    def test_create_tiktok(self):
        adapter = AdPlatformFactory.create(AdPlatform.TIKTOK)
        assert isinstance(adapter, TikTokAdsAdapter)

    def test_create_with_credentials(self):
        adapter = AdPlatformFactory.create(AdPlatform.GOOGLE_ADS, {"token": "x"})
        assert adapter.credentials == {"token": "x"}

    def test_create_unknown_platform_raises(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            AdPlatformFactory.create("unknown_platform")  # type: ignore

    def test_adapters_dict_contains_all(self):
        assert set(AdPlatformFactory._adapters.keys()) == {
            AdPlatform.GOOGLE_ADS, AdPlatform.META,
            AdPlatform.LINKEDIN, AdPlatform.TIKTOK,
        }

    @pytest.mark.asyncio
    async def test_get_connected_campaigns(self):
        connected = [
            {"platform": "google_ads", "platform_account_id": "acc-1", "credentials": {}},
            {"platform": "meta", "platform_account_id": "acc-2", "credentials": {}},
        ]
        result = await AdPlatformFactory.get_connected_campaigns(connected)
        assert len(result) == 3
        assert result[0].platform == AdPlatform.GOOGLE_ADS
        assert result[1].platform == AdPlatform.GOOGLE_ADS
        assert result[2].platform == AdPlatform.META
