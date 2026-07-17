from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )
    from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl



class AnalyticsService:
    def __init__(
        self,
        campaign_repo: CampaignRepositoryImpl,
        content_repo: ContentRepositoryImpl,
    ):
        self.campaign_repo = campaign_repo
        self.content_repo = content_repo

    async def get_overview(self, organization_id: UUID) -> dict:
        campaigns = await self.campaign_repo.find_by_organization(organization_id)
        contents = await self.content_repo.find_by_organization(organization_id)

        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.status == "active"])
        draft_campaigns = len([c for c in campaigns if c.status == "draft"])
        completed_campaigns = len([c for c in campaigns if c.status == "completed"])
        total_content = len(contents)
        published_content = len([c for c in contents if c.status == "published"])
        total_budget = sum(c.budget_amount or 0 for c in campaigns)

        status_breakdown = {}
        for c in campaigns:
            s = c.status
            status_breakdown[s] = status_breakdown.get(s, 0) + 1

        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "draft_campaigns": draft_campaigns,
            "completed_campaigns": completed_campaigns,
            "total_content": total_content,
            "published_content": published_content,
            "total_budget": total_budget,
            "status_breakdown": status_breakdown,
        }

    async def get_campaign_performance(self, organization_id: UUID) -> list[dict]:
        campaigns = await self.campaign_repo.find_by_organization(organization_id)
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "status": c.status,
                "budget": c.budget_amount or 0,
                "channels": c.channels,
                "spend": 0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "revenue": 0,
                "roi": 0,
            }
            for c in campaigns
        ]

    async def get_ad_performance(self, connected_accounts: list[dict]) -> dict:
        from app.infrastructure.external_adapters.adplatforms.base_adapter import AdPlatformFactory

        all_campaigns = await AdPlatformFactory.get_connected_campaigns(connected_accounts)

        total_impressions = sum(c.impressions for c in all_campaigns)
        total_clicks = sum(c.clicks for c in all_campaigns)
        total_spend = sum(c.spend for c in all_campaigns)
        total_conversions = sum(c.conversions for c in all_campaigns)
        total_revenue = sum(c.revenue for c in all_campaigns)
        total_budget = sum(c.budget for c in all_campaigns)

        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_spend": total_spend,
            "total_conversions": total_conversions,
            "total_revenue": total_revenue,
            "total_budget": total_budget,
            "ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "cpc": round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
            "conversion_rate": round(total_conversions / total_clicks * 100, 2)
            if total_clicks > 0
            else 0,
            "roi": round((total_revenue - total_spend) / total_spend * 100, 2)
            if total_spend > 0
            else 0,
            "platforms": [
                {
                    "name": platform,
                    "campaigns": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "spend": c.spend,
                            "impressions": c.impressions,
                            "clicks": c.clicks,
                            "conversions": c.conversions,
                            "revenue": c.revenue,
                        }
                        for c in all_campaigns
                        if c.platform.value == platform
                    ],
                }
                for platform in {c.platform.value for c in all_campaigns}
            ],
        }

    # ===== ADVANCED ANALYTICS METHODS =====

    async def get_campaign_funnel(self, campaign_id: UUID) -> dict:
        """Get funnel metrics for a specific campaign."""
        # Get campaign details
        campaign = await self.campaign_repo.find_by_id(campaign_id)
        if not campaign:
            return {}

        # In a real implementation, this would query actual funnel events
        # For now, return a structured funnel with mock data
        return {
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "stages": [
                {"stage": "impressions", "count": 0, "rate": 100.0},
                {"stage": "clicks", "count": 0, "rate": 0.0},
                {"stage": "landing_page_views", "count": 0, "rate": 0.0},
                {"stage": "form_starts", "count": 0, "rate": 0.0},
                {"stage": "form_completions", "count": 0, "rate": 0.0},
                {"stage": "qualified_leads", "count": 0, "rate": 0.0},
                {"stage": "opportunities", "count": 0, "rate": 0.0},
                {"stage": "closed_won", "count": 0, "rate": 0.0},
            ],
            "total_conversion_rate": 0.0,
            "avg_time_to_convert": None,
        }

    async def get_comparative_metrics(
        self,
        organization_id: UUID,
        period_type: str = "week",
    ) -> dict:
        """Get comparative metrics: current vs previous period."""
        end_date = datetime.utcnow()

        if period_type == "day":
            current_start = end_date - timedelta(days=1)
            previous_start = current_start - timedelta(days=1)
            previous_end = current_start
        elif period_type == "week":
            current_start = end_date - timedelta(weeks=1)
            previous_start = current_start - timedelta(weeks=1)
            previous_end = current_start
        elif period_type == "month":
            current_start = end_date - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
            previous_end = current_start
        elif period_type == "quarter":
            current_start = end_date - timedelta(days=90)
            previous_start = current_start - timedelta(days=90)
            previous_end = current_start
        else:
            current_start = end_date - timedelta(weeks=1)
            previous_start = current_start - timedelta(weeks=1)
            previous_end = current_start

        current_campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, current_start, end_date
        )
        previous_campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, previous_start, previous_end
        )

        def calc_metrics(camps):
            total = len(camps)
            active = len([c for c in camps if c.status == "active"])
            budget = sum(c.budget_amount or 0 for c in camps)
            return {"total": total, "active": active, "budget": float(budget)}

        current = calc_metrics(current_campaigns)
        previous = calc_metrics(previous_campaigns)

        changes = {}
        for key in current:
            prev = previous.get(key, 0)
            curr = current.get(key, 0)
            if prev > 0:
                changes[key] = round((curr - prev) / prev * 100, 2)
            else:
                changes[key] = 100.0 if curr > 0 else 0.0

        return {
            "current_period": current,
            "previous_period": previous,
            "changes": changes,
            "period_start": current_start,
            "period_end": end_date,
            "comparison_type": f"{period_type}_over_{period_type}",
        }

    async def get_revenue_attribution(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get revenue attribution by source/channel/campaign."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, start_date, end_date
        )

        # Mock attribution data - in production this would come from actual tracking
        items = []
        for c in campaigns:
            items.append({
                "source": "organic",
                "channel": c.channels[0] if c.channels else "unknown",
                "campaign_id": str(c.id),
                "campaign_name": c.name,
                "attributed_revenue": float(c.budget_amount or 0) * 0.1,  # Mock 10% revenue
                "attributed_conversions": 0,
                "touchpoint_count": 1,
                "confidence": 0.7,
            })

        total_attributed = sum(i["attributed_revenue"] for i in items)

        return {
            "items": items,
            "total_attributed_revenue": total_attributed,
            "unattributed_revenue": 0.0,
            "period_start": start_date,
            "period_end": end_date,
        }

    async def get_timeseries_data(
        self,
        organization_id: UUID,
        metric: str,
        granularity: str,
        days: int,
    ) -> dict:
        """Get time series data for a metric."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Determine interval
        if granularity == "hour":
            interval = timedelta(hours=1)
            fmt = "%Y-%m-%d %H:00"
        elif granularity == "day":
            interval = timedelta(days=1)
            fmt = "%Y-%m-%d"
        elif granularity == "week":
            interval = timedelta(weeks=1)
            fmt = "%Y-W%U"
        else:  # month
            interval = timedelta(days=30)
            fmt = "%Y-%m"

        points = []
        current = start_date
        while current <= end_date:
            # Mock data for demonstration
            if metric == "campaigns":
                value = len(await self.campaign_repo.find_by_organization_and_date_range(organization_id, current, current + interval))
            elif metric == "content":
                value = len(await self.content_repo.find_by_organization_and_date_range(organization_id, current, current + interval))
            else:
                value = 0

            points.append({
                "timestamp": current.isoformat(),
                "value": float(value),
                "label": current.strftime(fmt),
            })
            current += interval

        return {
            "metric": metric,
            "granularity": granularity,
            "points": points,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }
