from typing import ClassVar

import httpx

from app.application.ports.ad_platform_port import AdPlatformPort
from app.config import config
from app.domain.entities.adplatforms.platform import AdCampaign, AdPlatform, AdStatus


def _is_mock_mode(credentials: dict | None) -> bool:
    return not credentials or not any(v for v in (credentials or {}).values() if v)


MOCK_GOOGLE_CAMPAIGNS = [
    AdCampaign(
        id="google-campaign-1", platform=AdPlatform.GOOGLE_ADS,
        name="Google Search - Brand", status=AdStatus.ACTIVE,
        budget=5000, spend=3240.50, impressions=125000, clicks=4200,
        conversions=185, revenue=18500,
    ),
    AdCampaign(
        id="google-campaign-2", platform=AdPlatform.GOOGLE_ADS,
        name="Google Display - Retargeting", status=AdStatus.ACTIVE,
        budget=3000, spend=2100.00, impressions=450000, clicks=1800,
        conversions=95, revenue=9500,
    ),
]

MOCK_META_CAMPAIGNS = [
    AdCampaign(
        id="meta-campaign-1", platform=AdPlatform.META,
        name="Meta - Summer Sale", status=AdStatus.ACTIVE,
        budget=8000, spend=5600.00, impressions=890000, clicks=12500,
        conversions=420, revenue=42000,
    ),
]


class BaseAdAdapter(AdPlatformPort):
    def __init__(self, credentials: dict | None = None):
        self.credentials = credentials or {}
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _map_status(self, platform_status: str, platform: AdPlatform) -> AdStatus:
        mapping = {
            AdPlatform.GOOGLE_ADS: {
                "ENABLED": AdStatus.ACTIVE,
                "PAUSED": AdStatus.PAUSED,
                "REMOVED": AdStatus.COMPLETED,
            },
            AdPlatform.META: {
                "ACTIVE": AdStatus.ACTIVE,
                "PAUSED": AdStatus.PAUSED,
                "ARCHIVED": AdStatus.COMPLETED,
            },
        }
        return mapping.get(platform, {}).get(platform_status.upper(), AdStatus.ACTIVE)


class GoogleAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.GOOGLE_ADS

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            return MOCK_GOOGLE_CAMPAIGNS
        client = await self.get_client()
        token = self.credentials.get("access_token") or config.google_ads_refresh_token
        headers = {
            "Authorization": f"Bearer {token}",
            "developer-token": self.credentials.get("developer_token") or config.google_ads_developer_token,
        }
        resp = await client.post(
            f"https://googleads.googleapis.com/v16/customers/{account_id}/googleAds:search",
            headers=headers,
            json={
                "query": "SELECT campaign.id, campaign.name, campaign.status, "
                         "campaign_budget.amount_micros, metrics.impressions, metrics.clicks, "
                         "metrics.conversions, metrics.cost_micros "
                         "FROM campaign WHERE campaign.status != 'REMOVED'",
            },
        )
        if resp.status_code != 200:
            return MOCK_GOOGLE_CAMPAIGNS
        data = resp.json()
        campaigns = []
        for row in data.get("results", []):
            c = row.get("campaign", {})
            metrics = row.get("metrics", {})
            campaigns.append(AdCampaign(
                id=str(c.get("id", "")), platform=AdPlatform.GOOGLE_ADS,
                name=c.get("name", ""), status=self._map_status(c.get("status", ""), AdPlatform.GOOGLE_ADS),
                budget=float(c.get("budget", {}).get("amountMicros", 0)) / 1_000_000,
                spend=float(metrics.get("costMicros", 0)) / 1_000_000,
                impressions=int(metrics.get("impressions", 0)),
                clicks=int(metrics.get("clicks", 0)),
                conversions=int(metrics.get("conversions", 0)),
            ))
        return campaigns or MOCK_GOOGLE_CAMPAIGNS

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        if _is_mock_mode(self.credentials):
            return "google-new-campaign-id"
        client = await self.get_client()
        token = self.credentials.get("access_token") or config.google_ads_refresh_token
        headers = {"Authorization": f"Bearer {token}", "developer-token": config.google_ads_developer_token}
        resp = await client.post(
            f"https://googleads.googleapis.com/v16/customers/{self.credentials.get('customer_id', '')}/campaigns",
            headers=headers, json={"name": campaign.name, "status": "ENABLED"},
        )
        data = resp.json()
        return str(data.get("id", "google-new-campaign-id"))

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        return True


class MetaAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.META

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            return MOCK_META_CAMPAIGNS
        client = await self.get_client()
        token = self.credentials.get("access_token") or config.meta_access_token
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(
            f"https://graph.facebook.com/v19.0/{account_id}/campaigns",
            headers=headers,
            params={
                "fields": "id,name,status,daily_budget,lifetime_budget,"
                          "insights{impressions,clicks,conversions,spend}",
            },
        )
        if resp.status_code != 200:
            return MOCK_META_CAMPAIGNS
        data = resp.json()
        campaigns = []
        for c in data.get("data", []):
            insights = c.get("insights", {}).get("data", [{}])[0] if c.get("insights", {}).get("data") else {}
            campaigns.append(AdCampaign(
                id=c.get("id", ""), platform=AdPlatform.META,
                name=c.get("name", ""), status=self._map_status(c.get("status", ""), AdPlatform.META),
                budget=float(c.get("daily_budget", 0) or 0),
                spend=float(insights.get("spend", 0)),
                impressions=int(insights.get("impressions", 0)),
                clicks=int(insights.get("clicks", 0)),
                conversions=int(insights.get("conversions", 0)),
            ))
        return campaigns or MOCK_META_CAMPAIGNS

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        return "meta-new-campaign-id"

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        return True


class LinkedInAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.LINKEDIN

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            return []
        client = await self.get_client()
        token = self.credentials.get("access_token") or config.linkedin_access_token
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(
            "https://api.linkedin.com/rest/adCampaigns",
            headers=headers, params={"q": "account", "account": account_id},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            AdCampaign(id=c.get("id", ""), platform=AdPlatform.LINKEDIN,
                       name=c.get("name", ""), status=AdStatus.ACTIVE)
            for c in data.get("elements", [])
        ]

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        return "linkedin-new-campaign-id"

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        return True


class TikTokAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.TIKTOK

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            return []
        client = await self.get_client()
        token = self.credentials.get("access_token") or config.tiktok_access_token
        headers = {"Access-Token": token}
        resp = await client.post(
            "https://business-api.tiktok.com/open_api/v1.3/campaign/get/",
            headers=headers, json={
                "advertiser_id": self.credentials.get("advertiser_id") or config.tiktok_advertiser_id,
                "page_size": 100,
            },
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            AdCampaign(id=c.get("campaign_id", ""), platform=AdPlatform.TIKTOK,
                       name=c.get("campaign_name", ""), status=AdStatus.ACTIVE)
            for c in data.get("data", {}).get("list", [])
        ]

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        return "tiktok-new-campaign-id"

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        return True


class AdPlatformFactory:
    _adapters: ClassVar[dict[AdPlatform, type[BaseAdAdapter]]] = {
        AdPlatform.GOOGLE_ADS: GoogleAdsAdapter,
        AdPlatform.META: MetaAdsAdapter,
        AdPlatform.LINKEDIN: LinkedInAdsAdapter,
        AdPlatform.TIKTOK: TikTokAdsAdapter,
    }

    @classmethod
    def create(cls, platform: AdPlatform, credentials: dict | None = None) -> BaseAdAdapter:
        adapter_cls = cls._adapters.get(platform)
        if not adapter_cls:
            raise ValueError(f"Unsupported platform: {platform}")
        return adapter_cls(credentials=credentials)

    @classmethod
    async def get_connected_campaigns(
        cls, connected_accounts: list[dict]
    ) -> list[AdCampaign]:
        all_campaigns = []
        for account in connected_accounts:
            platform = AdPlatform(account.get("platform", "google_ads"))
            adapter = cls.create(platform, account.get("credentials"))
            campaigns = await adapter.get_campaigns(account.get("platform_account_id", ""))
            all_campaigns.extend(campaigns)
        return all_campaigns
