import csv
import io
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.analytics.analytics_service import AnalyticsService
from app.infrastructure.db.models.advertising.advertising_models import (
    AdInsightModel,
)
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.content.content_model import ContentModel
from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl


class ReportingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics = AnalyticsService(
            campaign_repo=CampaignRepositoryImpl(session),
            content_repo=ContentRepositoryImpl(session),
        )

    async def get_trends(
        self,
        organization_id: UUID,
        metric: str = "spend",
        days: int = 30,
    ) -> dict:
        end = datetime.now(UTC).date()
        start = end - timedelta(days=days)

        stmt = (
            select(
                AdInsightModel.date,
                func.sum(getattr(AdInsightModel, metric, AdInsightModel.spend)).label("value"),
            )
            .where(
                AdInsightModel.organization_id == organization_id,
                AdInsightModel.date >= start.isoformat(),
                AdInsightModel.date <= end.isoformat(),
            )
            .group_by(AdInsightModel.date)
            .order_by(AdInsightModel.date)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        daily = {row.date: float(row.value) for row in rows}
        filled = []
        for i in range(days + 1):
            d = (start + timedelta(days=i)).isoformat()
            filled.append({"date": d, "value": daily.get(d, 0)})

        values = [v["value"] for v in filled]
        avg = sum(values) / max(len(values), 1)
        peak = max(values) if values else 0

        return {
            "metric": metric,
            "days": days,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": filled,
            "average": round(avg, 2),
            "peak": peak,
            "total": round(sum(values), 2),
        }

    async def get_campaign_timeline(
        self,
        organization_id: UUID,
        campaign_ids: list[UUID],
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        stmt = (
            select(AdInsightModel)
            .where(
                AdInsightModel.organization_id == organization_id,
                AdInsightModel.ad_campaign_id.in_(campaign_ids),
                AdInsightModel.date >= start_date,
                AdInsightModel.date <= end_date,
            )
            .order_by(AdInsightModel.date)
        )
        result = await self.session.execute(stmt)
        insights = result.scalars().all()

        grouped: dict[str, list[dict]] = {}
        for ins in insights:
            cid = str(ins.ad_campaign_id)
            if cid not in grouped:
                grouped[cid] = []
            grouped[cid].append(
                {
                    "date": ins.date,
                    "impressions": ins.impressions,
                    "clicks": ins.clicks,
                    "spend": float(ins.spend),
                    "conversions": ins.conversions,
                    "revenue": float(ins.revenue),
                }
            )

        return [{"ad_campaign_id": cid, "data": points} for cid, points in grouped.items()]

    async def get_platform_comparison(self, organization_id: UUID) -> dict:
        stmt = (
            select(
                AdInsightModel.platform,
                func.sum(AdInsightModel.impressions).label("impressions"),
                func.sum(AdInsightModel.clicks).label("clicks"),
                func.sum(AdInsightModel.spend).label("spend"),
                func.sum(AdInsightModel.conversions).label("conversions"),
                func.sum(AdInsightModel.revenue).label("revenue"),
            )
            .where(AdInsightModel.organization_id == organization_id)
            .group_by(AdInsightModel.platform)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        platforms = [
            {
                "platform": row.platform or "unknown",
                "impressions": int(row.impressions),
                "clicks": int(row.clicks),
                "spend": round(float(row.spend), 2),
                "conversions": int(row.conversions),
                "revenue": round(float(row.revenue), 2),
                "ctr": round((row.clicks / row.impressions * 100) if row.impressions else 0, 2),
                "cpc": round((row.spend / row.clicks) if row.clicks else 0, 2),
                "roas": round((row.revenue / row.spend) if row.spend else 0, 2),
            }
            for row in rows
        ]

        return {"platforms": platforms, "total_platforms": len(platforms)}

    async def _export_campaigns(self, writer: csv.writer, organization_id: UUID) -> None:
        writer.writerow(
            ["ID", "Name", "Status", "Budget", "Start Date", "End Date", "Channels", "Objective"]
        )
        stmt = select(CampaignModel).where(CampaignModel.organization_id == organization_id)
        result = await self.session.execute(stmt)
        for c in result.scalars().all():
            writer.writerow(
                [
                    str(c.id),
                    c.name,
                    c.status,
                    c.budget_amount or 0,
                    c.start_date.isoformat() if c.start_date else "",
                    c.end_date.isoformat() if c.end_date else "",
                    ", ".join(c.channels) if c.channels else "",
                    c.objective or "",
                ]
            )

    async def _export_content(self, writer: csv.writer, organization_id: UUID) -> None:
        writer.writerow(["ID", "Title", "Type", "Status", "Version", "Created At", "Scheduled At"])
        stmt = select(ContentModel).where(ContentModel.organization_id == organization_id)
        result = await self.session.execute(stmt)
        for c in result.scalars().all():
            writer.writerow(
                [
                    str(c.id),
                    c.title,
                    c.content_type,
                    c.status,
                    c.version,
                    c.created_at.isoformat() if c.created_at else "",
                    c.scheduled_at.isoformat() if c.scheduled_at else "",
                ]
            )

    async def _export_ads(
        self,
        writer: csv.writer,
        organization_id: UUID,
        start_date: str | None,
        end_date: str | None,
    ) -> None:
        writer.writerow(
            [
                "Date",
                "Platform",
                "Campaign ID",
                "Impressions",
                "Clicks",
                "Spend",
                "Conversions",
                "Revenue",
            ]
        )
        stmt = select(AdInsightModel).where(
            AdInsightModel.organization_id == organization_id,
        )
        if start_date:
            stmt = stmt.where(AdInsightModel.date >= start_date)
        if end_date:
            stmt = stmt.where(AdInsightModel.date <= end_date)
        stmt = stmt.order_by(AdInsightModel.date)
        result = await self.session.execute(stmt)
        for ins in result.scalars().all():
            writer.writerow(
                [
                    ins.date,
                    ins.platform or "",
                    str(ins.ad_campaign_id) if ins.ad_campaign_id else "",
                    ins.impressions,
                    ins.clicks,
                    ins.spend,
                    ins.conversions,
                    ins.revenue,
                ]
            )

    async def _export_ad_accounts(self, writer: csv.writer, organization_id: UUID) -> None:
        writer.writerow(["ID", "Platform", "Account Name", "Status", "Last Synced"])
        from app.infrastructure.db.models.advertising.advertising_models import AdAccountModel

        stmt = select(AdAccountModel).where(AdAccountModel.organization_id == organization_id)
        result = await self.session.execute(stmt)
        for a in result.scalars().all():
            writer.writerow(
                [
                    str(a.id),
                    a.platform,
                    a.account_name,
                    a.status,
                    a.last_synced_at.isoformat() if a.last_synced_at else "",
                ]
            )

    async def export_csv(
        self,
        report_type: str,
        organization_id: UUID,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "campaigns":
            await self._export_campaigns(writer, organization_id)
        elif report_type == "content":
            await self._export_content(writer, organization_id)
        elif report_type == "ads":
            await self._export_ads(writer, organization_id, start_date, end_date)
        elif report_type == "ad_accounts":
            await self._export_ad_accounts(writer, organization_id)

        return output.getvalue()
