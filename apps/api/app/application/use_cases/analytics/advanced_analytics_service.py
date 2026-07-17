from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.infrastructure.db.repositories.campaigns.campaign_repository import (
        CampaignRepositoryImpl,
    )
    from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl


class AdvancedAnalyticsService:
    """Advanced analytics service with time-series, funnel, comparative, and revenue attribution."""

    def __init__(
        self,
        campaign_repo: "CampaignRepositoryImpl",
        content_repo: "ContentRepositoryImpl",
    ):
        self.campaign_repo = campaign_repo
        self.content_repo = content_repo

    async def get_overview(self, organization_id: UUID) -> dict:
        """Get basic overview metrics."""
        campaigns = await self.campaign_repo.find_by_organization(organization_id)
        contents = await self.content_repo.find_by_organization(organization_id)

        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.status == "active"])
        draft_campaigns = len([c for c in campaigns if c.status == "draft"])
        completed_campaigns = len([c for c in campaigns if c.status == "completed"])
        total_content = len(contents)
        published_content = len([c for c in contents if c.status == "published"])
        total_budget = sum(Decimal(str(c.budget_amount or 0)) for c in campaigns)

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
            "total_budget": float(total_budget),
            "status_breakdown": status_breakdown,
        }

    async def get_timeseries(
        self,
        organization_id: UUID,
        metric: str,
        granularity: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Get time-series data for a metric."""
        campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, start_date, end_date
        )
        contents = await self.content_repo.find_by_organization_and_date_range(
            organization_id, start_date, end_date
        )

        # Generate time buckets
        points = []
        current = start_date
        delta = self._get_granularity_delta(granularity)

        while current <= end_date:
            next_bucket = current + delta
            bucket_campaigns = [c for c in campaigns if current <= c.created_at < next_bucket]
            bucket_contents = [c for c in contents if current <= c.created_at < next_bucket]

            value = self._calculate_metric_value(metric, bucket_campaigns, bucket_contents)
            points.append({
                "timestamp": current,
                "value": float(value),
                "label": self._format_timestamp(current, granularity),
            })
            current = next_bucket

        return points

    def _get_granularity_delta(self, granularity: str) -> timedelta:
        if granularity == "hour":
            return timedelta(hours=1)
        if granularity == "day":
            return timedelta(days=1)
        if granularity == "week":
            return timedelta(weeks=1)
        if granularity == "month":
            return timedelta(days=30)  # Approximation
        return timedelta(days=1)

    def _calculate_metric_value(self, metric: str, campaigns: list, contents: list) -> Decimal:
        if metric == "campaigns":
            return Decimal(len(campaigns))
        if metric == "content":
            return Decimal(len(contents))
        if metric == "spend":
            return sum(Decimal(str(c.budget_amount or 0)) for c in campaigns)
        if metric == "revenue":
            # Placeholder - would come from ad platforms
            return Decimal(0)
        if metric == "overview":
            return Decimal(len(campaigns) + len(contents))
        return Decimal(0)

    def _format_timestamp(self, dt: datetime, granularity: str) -> str:
        if granularity == "hour":
            return dt.strftime("%Y-%m-%d %H:00")
        if granularity == "day":
            return dt.strftime("%Y-%m-%d")
        if granularity == "week":
            return dt.strftime("%Y-W%U")
        if granularity == "month":
            return dt.strftime("%Y-%m")
        return dt.strftime("%Y-%m-%d")

    async def get_campaign_funnel(self, campaign_id: UUID) -> dict:
        """Get conversion funnel for a campaign."""
        # This would normally query ad platform data
        # For now, return a structured funnel template
        return {
            "campaign_id": str(campaign_id),
            "campaign_name": "Campaign",  # Would fetch actual name
            "stages": [
                {
                    "stage": "impressions",
                    "count": 0,
                    "conversion_rate": 100.0,
                    "dropoff_rate": 0.0,
                },
                {
                    "stage": "clicks",
                    "count": 0,
                    "conversion_rate": 0.0,
                    "dropoff_rate": 0.0,
                },
                {
                    "stage": "landing_page_views",
                    "count": 0,
                    "conversion_rate": 0.0,
                    "dropoff_rate": 0.0,
                },
                {
                    "stage": "conversions",
                    "count": 0,
                    "conversion_rate": 0.0,
                    "dropoff_rate": 0.0,
                },
            ],
            "overall_conversion": 0.0,
            "period_start": datetime.utcnow() - timedelta(days=30),
            "period_end": datetime.utcnow(),
        }

    async def get_comparative_metrics(
        self,
        organization_id: UUID,
        period_type: str = "week",
    ) -> dict:
        """Get comparative metrics (current vs previous period)."""
        now = datetime.utcnow()

        if period_type == "day":
            current_start = now - timedelta(days=1)
            current_end = now
            previous_start = now - timedelta(days=2)
            previous_end = now - timedelta(days=1)
        elif period_type == "week":
            current_start = now - timedelta(weeks=1)
            current_end = now
            previous_start = now - timedelta(weeks=2)
            previous_end = now - timedelta(weeks=1)
        elif period_type == "month":
            current_start = now - timedelta(days=30)
            current_end = now
            previous_start = now - timedelta(days=60)
            previous_end = now - timedelta(days=30)
        elif period_type == "quarter":
            current_start = now - timedelta(days=90)
            current_end = now
            previous_start = now - timedelta(days=180)
            previous_end = now - timedelta(days=90)
        else:
            current_start = now - timedelta(weeks=1)
            current_end = now
            previous_start = now - timedelta(weeks=2)
            previous_end = now - timedelta(weeks=1)

        current_campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, current_start, current_end
        )
        previous_campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, previous_start, previous_end
        )

        current_content = await self.content_repo.find_by_organization_and_date_range(
            organization_id, current_start, current_end
        )
        previous_content = await self.content_repo.find_by_organization_and_date_range(
            organization_id, previous_start, previous_end
        )

        current_budget = sum(Decimal(str(c.budget_amount or 0)) for c in current_campaigns)
        previous_budget = sum(Decimal(str(c.budget_amount or 0)) for c in previous_campaigns)

        def calc_change(current: float, previous: float) -> dict:
            if previous == 0:
                return {"absolute": current, "percent": 100.0 if current > 0 else 0.0}
            return {
                "absolute": current - previous,
                "percent": round((current - previous) / previous * 100, 2),
            }

        return {
            "current_period": {
                "campaigns_created": len(current_campaigns),
                "content_created": len(current_content),
                "total_budget": float(current_budget),
                "active_campaigns": len([c for c in current_campaigns if c.status == "active"]),
            },
            "previous_period": {
                "campaigns_created": len(previous_campaigns),
                "content_created": len(previous_content),
                "total_budget": float(previous_budget),
                "active_campaigns": len([c for c in previous_campaigns if c.status == "active"]),
            },
            "changes": {
                "campaigns_created": calc_change(len(current_campaigns), len(previous_campaigns)),
                "content_created": calc_change(len(current_content), len(previous_content)),
                "total_budget": calc_change(float(current_budget), float(previous_budget)),
                "active_campaigns": calc_change(
                    len([c for c in current_campaigns if c.status == "active"]),
                    len([c for c in previous_campaigns if c.status == "active"]),
                ),
            },
            "period_start": current_start,
            "period_end": current_end,
            "comparison_type": f"{period_type}_over_{period_type}",
        }

    async def get_revenue_attribution(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get revenue attribution by channel/campaign."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        campaigns = await self.campaign_repo.find_by_organization_and_date_range(
            organization_id, start_date, end_date
        )

        # This would normally integrate with ad platform data
        # For now, return a structured response template
        attribution_items = []
        total_revenue = Decimal(0)

        for c in campaigns:
            # Mock attribution data - in production this would come from ad platforms
            item = {
                "source": "organic",
                "channel": c.channels[0] if c.channels else "unknown",
                "campaign_id": str(c.id),
                "campaign_name": c.name,
                "attributed_revenue": 0.0,
                "attributed_conversions": 0,
                "touchpoint_count": 1,
                "confidence": 0.8,
            }
            attribution_items.append(item)

        return {
            "items": attribution_items,
            "total_attributed_revenue": float(total_revenue),
            "unattributed_revenue": 0.0,
            "period_start": start_date,
            "period_end": end_date,
        }
