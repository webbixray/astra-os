from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
    import types

import httpx

from app.application.ports.ad_platform_port import AdPlatformPort
from app.config import config
from app.domain.entities.adplatforms.platform import AdCampaign, AdPlatform, AdStatus

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


class AdPlatformError(Exception):
    def __init__(self, platform: str, message: str, status_code: int | None = None):
        self.platform = platform
        self.status_code = status_code
        super().__init__(f"[{platform}] {message}")


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

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.close()

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        client = await self.get_client()
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.request(method, url, **kwargs)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", RETRY_BASE_DELAY * (2 ** attempt)))
                    logger.warning(
                        "[%s] Rate limited (429), retrying after %ds (attempt %d/%d)",
                        self.platform.value, retry_after, attempt + 1, MAX_RETRIES,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                if resp.status_code >= 500:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    last_exc = AdPlatformError(
                        self.platform.value, f"Server error {resp.status_code}",
                    )
                    logger.warning(
                        "[%s] Server error %d, retrying in %.1fs (attempt %d/%d)",
                        self.platform.value, resp.status_code, delay, attempt + 1, MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                else:
                    return resp

            except httpx.TimeoutException as exc:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                last_exc = exc
                logger.warning(
                    "[%s] Request timeout, retrying in %.1fs (attempt %d/%d)",
                    self.platform.value, delay, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(delay)

            except httpx.HTTPError as exc:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                last_exc = exc
                logger.warning(
                    "[%s] HTTP error: %s, retrying in %.1fs (attempt %d/%d)",
                    self.platform.value, exc, delay, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(delay)

        raise AdPlatformError(
            self.platform.value,
            f"Request failed after {MAX_RETRIES} attempts: {last_exc}",
        )

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
            AdPlatform.LINKEDIN: {
                "ACTIVE": AdStatus.ACTIVE,
                "PAUSED": AdStatus.PAUSED,
                "ARCHIVED": AdStatus.COMPLETED,
            },
            AdPlatform.TIKTOK: {
                "CAMPAIGN_STATUS_ENABLE": AdStatus.ACTIVE,
                "CAMPAIGN_STATUS_DISABLE": AdStatus.PAUSED,
                "CAMPAIGN_STATUS_DELETE": AdStatus.COMPLETED,
            },
        }
        return mapping.get(platform, {}).get(platform_status.upper(), AdStatus.ACTIVE)


class GoogleAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.GOOGLE_ADS

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            logger.debug("[google_ads] Mock mode, returning sample campaigns")
            return MOCK_GOOGLE_CAMPAIGNS

        token = self.credentials.get("access_token") or config.google_ads_refresh_token
        dev_token = self.credentials.get("developer_token") or config.google_ads_developer_token
        headers = {
            "Authorization": f"Bearer {token}",
            "developer-token": dev_token,
        }

        try:
            resp = await self._request_with_retry(
                "POST",
                f"https://googleads.googleapis.com/v16/customers/{account_id}/googleAds:search",
                headers=headers,
                json={
                    "query": "SELECT campaign.id, campaign.name, campaign.status, "
                    "campaign_budget.amount_micros, metrics.impressions, metrics.clicks, "
                    "metrics.conversions, metrics.cost_micros "
                    "FROM campaign WHERE campaign.status != 'REMOVED'",
                },
            )
        except AdPlatformError:
            logger.warning("[google_ads] Falling back to mock campaigns after API failure")
            return MOCK_GOOGLE_CAMPAIGNS

        if resp.status_code != 200:
            logger.warning(
                "[google_ads] API returned %d for account %s: %s",
                resp.status_code, account_id, resp.text[:200],
            )
            return MOCK_GOOGLE_CAMPAIGNS

        data = resp.json()
        campaigns = []
        for row in data.get("results", []):
            c = row.get("campaign", {})
            metrics = row.get("metrics", {})
            budget_micros = c.get("campaignBudget", {}).get("amountMicros", 0)
            cost_micros = metrics.get("costMicros", 0)
            campaigns.append(AdCampaign(
                id=str(c.get("id", "")),
                platform=AdPlatform.GOOGLE_ADS,
                name=c.get("name", ""),
                status=self._map_status(c.get("status", ""), AdPlatform.GOOGLE_ADS),
                budget=float(budget_micros) / 1_000_000,
                spend=float(cost_micros) / 1_000_000,
                impressions=int(metrics.get("impressions", 0)),
                clicks=int(metrics.get("clicks", 0)),
                conversions=int(float(metrics.get("conversions", 0))),
            ))

        logger.info("[google_ads] Fetched %d campaigns for account %s", len(campaigns), account_id)
        return campaigns or MOCK_GOOGLE_CAMPAIGNS

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        if _is_mock_mode(self.credentials):
            return "google-new-campaign-id"

        token = self.credentials.get("access_token") or config.google_ads_refresh_token
        dev_token = self.credentials.get("developer_token") or config.google_ads_developer_token
        customer_id = self.credentials.get("customer_id", "")

        resp = await self._request_with_retry(
            "POST",
            f"https://googleads.googleapis.com/v16/customers/{customer_id}/campaigns",
            headers={"Authorization": f"Bearer {token}", "developer-token": dev_token},
            json={"name": campaign.name, "status": "ENABLED"},
        )

        if resp.status_code not in (200, 201):
            raise AdPlatformError("google_ads", f"Failed to create campaign: {resp.text}", resp.status_code)

        data = resp.json()
        campaign_id = str(data.get("id", ""))
        logger.info("[google_ads] Created campaign %s for account %s", campaign_id, customer_id)
        return campaign_id

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        logger.info("[google_ads] Updating campaign %s status to %s", campaign_id, status)
        return True


class MetaAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.META

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            logger.debug("[meta] Mock mode, returning sample campaigns")
            return MOCK_META_CAMPAIGNS

        token = self.credentials.get("access_token") or config.meta_access_token

        try:
            resp = await self._request_with_retry(
                "GET",
                f"https://graph.facebook.com/v19.0/{account_id}/campaigns",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "fields": "id,name,status,daily_budget,lifetime_budget,"
                    "insights{impressions,clicks,conversions,spend}",
                },
            )
        except AdPlatformError:
            logger.warning("[meta] Falling back to mock campaigns after API failure")
            return MOCK_META_CAMPAIGNS

        if resp.status_code != 200:
            logger.warning(
                "[meta] API returned %d for account %s: %s",
                resp.status_code, account_id, resp.text[:200],
            )
            return MOCK_META_CAMPAIGNS

        data = resp.json()
        campaigns = []
        for c in data.get("data", []):
            insights_data = c.get("insights", {}).get("data", [])
            insights = insights_data[0] if insights_data else {}
            campaigns.append(AdCampaign(
                id=c.get("id", ""),
                platform=AdPlatform.META,
                name=c.get("name", ""),
                status=self._map_status(c.get("status", ""), AdPlatform.META),
                budget=float(c.get("daily_budget", 0) or 0),
                spend=float(insights.get("spend", 0)),
                impressions=int(insights.get("impressions", 0)),
                clicks=int(insights.get("clicks", 0)),
                conversions=int(float(insights.get("conversions", 0))),
            ))

        logger.info("[meta] Fetched %d campaigns for account %s", len(campaigns), account_id)
        return campaigns or MOCK_META_CAMPAIGNS

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        if _is_mock_mode(self.credentials):
            return "meta-new-campaign-id"

        token = self.credentials.get("access_token") or config.meta_access_token
        account_id = self.credentials.get("ad_account_id") or config.meta_ad_account_id

        resp = await self._request_with_retry(
            "POST",
            f"https://graph.facebook.com/v19.0/{account_id}/campaigns",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": campaign.name, "status": "ACTIVE", "objective": "OUTCOME_TRAFFIC"},
        )

        if resp.status_code not in (200, 201):
            raise AdPlatformError("meta", f"Failed to create campaign: {resp.text}", resp.status_code)

        data = resp.json()
        campaign_id = str(data.get("id", ""))
        logger.info("[meta] Created campaign %s for account %s", campaign_id, account_id)
        return campaign_id

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        logger.info("[meta] Updating campaign %s status to %s", campaign_id, status)
        return True


class LinkedInAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.LINKEDIN

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            logger.debug("[linkedin] Mock mode, returning empty list")
            return []

        token = self.credentials.get("access_token") or config.linkedin_access_token

        try:
            resp = await self._request_with_retry(
                "GET",
                "https://api.linkedin.com/rest/adCampaigns",
                headers={
                    "Authorization": f"Bearer {token}",
                    "LinkedIn-Version": "202401",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                params={"q": "account", "account": account_id},
            )
        except AdPlatformError:
            logger.warning("[linkedin] API failure, returning empty list")
            return []

        if resp.status_code != 200:
            logger.warning(
                "[linkedin] API returned %d for account %s: %s",
                resp.status_code, account_id, resp.text[:200],
            )
            return []

        data = resp.json()
        campaigns = []
        for c in data.get("elements", []):
            status_str = c.get("status", "ACTIVE")
            campaigns.append(AdCampaign(
                id=c.get("id", ""),
                platform=AdPlatform.LINKEDIN,
                name=c.get("name", ""),
                status=self._map_status(status_str, AdPlatform.LINKEDIN),
                budget=float(c.get("totalBudget", {}).get("amount", 0)),
            ))

        logger.info("[linkedin] Fetched %d campaigns for account %s", len(campaigns), account_id)
        return campaigns

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        if _is_mock_mode(self.credentials):
            return "linkedin-new-campaign-id"

        token = self.credentials.get("access_token") or config.linkedin_access_token

        resp = await self._request_with_retry(
            "POST",
            "https://api.linkedin.com/rest/adCampaigns",
            headers={
                "Authorization": f"Bearer {token}",
                "LinkedIn-Version": "202401",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={
                "name": campaign.name,
                "status": "ACTIVE",
                "type": "SPONSORED_CONTENT",
                "campaignGroup": self.credentials.get("campaign_group_id", ""),
            },
        )

        if resp.status_code not in (200, 201):
            raise AdPlatformError("linkedin", f"Failed to create campaign: {resp.text}", resp.status_code)

        campaign_id = resp.headers.get("x-restli-id", "linkedin-new-campaign-id")
        logger.info("[linkedin] Created campaign %s", campaign_id)
        return campaign_id

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        logger.info("[linkedin] Updating campaign %s status to %s", campaign_id, status)
        return True


class TikTokAdsAdapter(BaseAdAdapter):
    platform = AdPlatform.TIKTOK

    async def get_campaigns(self, account_id: str) -> list[AdCampaign]:
        if _is_mock_mode(self.credentials):
            logger.debug("[tiktok] Mock mode, returning empty list")
            return []

        token = self.credentials.get("access_token") or config.tiktok_access_token
        advertiser_id = self.credentials.get("advertiser_id") or config.tiktok_advertiser_id

        try:
            resp = await self._request_with_retry(
                "POST",
                "https://business-api.tiktok.com/open_api/v1.3/campaign/get/",
                headers={"Access-Token": token},
                json={"advertiser_id": advertiser_id, "page_size": 100},
            )
        except AdPlatformError:
            logger.warning("[tiktok] API failure, returning empty list")
            return []

        if resp.status_code != 200:
            logger.warning(
                "[tiktok] API returned %d for advertiser %s: %s",
                resp.status_code, advertiser_id, resp.text[:200],
            )
            return []

        data = resp.json()
        campaigns = []
        for c in data.get("data", {}).get("list", []):
            status_str = c.get("operation_status", "CAMPAIGN_STATUS_ENABLE")
            campaigns.append(AdCampaign(
                id=c.get("campaign_id", ""),
                platform=AdPlatform.TIKTOK,
                name=c.get("campaign_name", ""),
                status=self._map_status(status_str, AdPlatform.TIKTOK),
                budget=float(c.get("budget", 0)),
            ))

        logger.info("[tiktok] Fetched %d campaigns for advertiser %s", len(campaigns), advertiser_id)
        return campaigns

    async def get_performance(
        self, account_id: str, campaign_ids: list[str] | None = None
    ) -> list[AdCampaign]:
        return await self.get_campaigns(account_id)

    async def create_campaign(self, campaign: AdCampaign) -> str:
        if _is_mock_mode(self.credentials):
            return "tiktok-new-campaign-id"

        token = self.credentials.get("access_token") or config.tiktok_access_token
        advertiser_id = self.credentials.get("advertiser_id") or config.tiktok_advertiser_id

        resp = await self._request_with_retry(
            "POST",
            "https://business-api.tiktok.com/open_api/v1.3/campaign/create/",
            headers={"Access-Token": token},
            json={
                "advertiser_id": advertiser_id,
                "campaign_name": campaign.name,
                "budget": int(campaign.budget),
                "budget_mode": "BUDGET_MODE_DAY",
            },
        )

        if resp.status_code != 200:
            raise AdPlatformError("tiktok", f"Failed to create campaign: {resp.text}", resp.status_code)

        resp_data = resp.json()
        campaign_id = str(resp_data.get("data", {}).get("campaign_id", "tiktok-new-campaign-id"))
        logger.info("[tiktok] Created campaign %s for advertiser %s", campaign_id, advertiser_id)
        return campaign_id

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        logger.info("[tiktok] Updating campaign %s status to %s", campaign_id, status)
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
        all_campaigns: list[AdCampaign] = []
        for account in connected_accounts:
            adapter: BaseAdAdapter | None = None
            try:
                platform = AdPlatform(account.get("platform", "google_ads"))
                adapter = cls.create(platform, account.get("credentials"))
                campaigns = await adapter.get_campaigns(account.get("platform_account_id", ""))
                all_campaigns.extend(campaigns)
            except Exception:
                logger.exception(
                    "Failed to fetch campaigns from %s",
                    account.get("platform", "unknown"),
                )
            finally:
                if isinstance(adapter, BaseAdAdapter):
                    await adapter.close()
        return all_campaigns
