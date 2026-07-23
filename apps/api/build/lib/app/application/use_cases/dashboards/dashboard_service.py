import statistics
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.common import now
from app.domain.entities.dashboards.dashboard import Dashboard, DashboardWidget
from app.domain.exceptions.domain_exceptions import EntityNotFoundError
from app.infrastructure.db.models.advertising.advertising_models import AdInsightModel
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.content.content_model import ContentModel
from app.infrastructure.db.models.email.email_campaign_model import EmailCampaignModel


class DashboardRepository:
    async def save(self, dashboard: Dashboard) -> Dashboard: ...
    async def find_by_id(self, dashboard_id: UUID) -> Dashboard | None: ...
    async def find_by_organization(self, org_id: UUID) -> list[Dashboard]: ...
    async def find_default(self, org_id: UUID) -> Dashboard | None: ...
    async def delete(self, dashboard_id: UUID) -> None: ...


class DashboardWidgetRepository:
    async def save(self, widget: DashboardWidget) -> DashboardWidget: ...
    async def find_by_dashboard(self, dashboard_id: UUID) -> list[DashboardWidget]: ...
    async def find_by_id(self, widget_id: UUID) -> DashboardWidget | None: ...
    async def delete(self, widget_id: UUID) -> None: ...
    async def delete_by_dashboard(self, dashboard_id: UUID) -> None: ...


# ── Metric Queries ──────────────────────────────────────────────────────────


async def _metric_campaigns_total(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(select(func.count()).where(CampaignModel.organization_id == org_id))
    return result.scalar() or 0


async def _metric_campaigns_active(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).where(
            CampaignModel.organization_id == org_id,
            CampaignModel.status == "active",
        )
    )
    return result.scalar() or 0


async def _metric_campaigns_by_status(db: AsyncSession, org_id: UUID) -> dict:
    rows = await db.execute(
        select(CampaignModel.status, func.count())
        .where(CampaignModel.organization_id == org_id)
        .group_by(CampaignModel.status)
    )
    return {row[0]: row[1] for row in rows.all()}


async def _metric_ad_sum(db: AsyncSession, org_id: UUID, since: datetime, column) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(column), 0)).where(
            AdInsightModel.organization_id == org_id, AdInsightModel.date >= since
        )
    )
    return float(result.scalar() or 0)


async def _metric_ad_spend(db: AsyncSession, org_id: UUID, since: datetime) -> float:
    return await _metric_ad_sum(db, org_id, since, AdInsightModel.spend)


async def _metric_ad_impressions(db: AsyncSession, org_id: UUID, since: datetime) -> int:
    return int(await _metric_ad_sum(db, org_id, since, AdInsightModel.impressions))


async def _metric_ad_clicks(db: AsyncSession, org_id: UUID, since: datetime) -> int:
    return int(await _metric_ad_sum(db, org_id, since, AdInsightModel.clicks))


async def _metric_ad_conversions(db: AsyncSession, org_id: UUID, since: datetime) -> int:
    return int(await _metric_ad_sum(db, org_id, since, AdInsightModel.conversions))


async def _metric_ad_ctr(db: AsyncSession, org_id: UUID, since: datetime) -> float:
    impr = await _metric_ad_impressions(db, org_id, since)
    clk = await _metric_ad_clicks(db, org_id, since)
    return (clk / impr * 100) if impr > 0 else 0.0


async def _metric_ad_spend_trend(db: AsyncSession, org_id: UUID, since: datetime) -> list:
    rows = await db.execute(
        select(AdInsightModel.date, func.coalesce(func.sum(AdInsightModel.spend), 0))
        .where(AdInsightModel.organization_id == org_id, AdInsightModel.date >= since)
        .group_by(AdInsightModel.date)
        .order_by(AdInsightModel.date)
    )
    return [{"date": str(row[0]), "value": float(row[1])} for row in rows.all()]


async def _metric_content_published(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).where(
            ContentModel.organization_id == org_id,
            ContentModel.status == "published",
        )
    )
    return result.scalar() or 0


async def _metric_content_by_type(db: AsyncSession, org_id: UUID) -> dict:
    rows = await db.execute(
        select(ContentModel.content_type, func.count())
        .where(ContentModel.organization_id == org_id)
        .group_by(ContentModel.content_type)
    )
    return {row[0]: row[1] for row in rows.all()}


async def _metric_email_sent(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(EmailCampaignModel.sent_count), 0)).where(
            EmailCampaignModel.organization_id == org_id
        )
    )
    return int(result.scalar() or 0)


async def _metric_email_open_rate(db: AsyncSession, org_id: UUID) -> float:
    sent_r = await db.execute(
        select(func.coalesce(func.sum(EmailCampaignModel.sent_count), 0)).where(
            EmailCampaignModel.organization_id == org_id
        )
    )
    open_r = await db.execute(
        select(func.coalesce(func.sum(EmailCampaignModel.open_count), 0)).where(
            EmailCampaignModel.organization_id == org_id
        )
    )
    sent = int(sent_r.scalar() or 0)
    opens = int(open_r.scalar() or 0)
    return (opens / sent * 100) if sent > 0 else 0.0


async def _metric_email_campaigns(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).where(EmailCampaignModel.organization_id == org_id)
    )
    return result.scalar() or 0


_METRIC_HANDLERS: dict[str, tuple] = {
    "campaigns_total": (_metric_campaigns_total, False),
    "campaigns_active": (_metric_campaigns_active, False),
    "campaigns_by_status": (_metric_campaigns_by_status, False),
    "ad_spend": (_metric_ad_spend, True),
    "ad_impressions": (_metric_ad_impressions, True),
    "ad_clicks": (_metric_ad_clicks, True),
    "ad_conversions": (_metric_ad_conversions, True),
    "ad_ctr": (_metric_ad_ctr, True),
    "ad_spend_trend": (_metric_ad_spend_trend, True),
    "content_published": (_metric_content_published, False),
    "content_by_type": (_metric_content_by_type, False),
    "email_sent": (_metric_email_sent, False),
    "email_open_rate": (_metric_email_open_rate, False),
    "email_campaigns": (_metric_email_campaigns, False),
}


async def query_metric(db: AsyncSession, org_id: UUID, metric: str, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    handler = _METRIC_HANDLERS.get(metric)
    if handler is None:
        return {"value": 0, "metric": metric}
    fn, needs_since = handler
    value = await fn(db, org_id, since) if needs_since else await fn(db, org_id)
    return {"value": value, "metric": metric}


# ── Anomaly Detection ────────────────────────────────────────────────────────


async def detect_anomalies(
    db: AsyncSession, org_id: UUID, metric: str = "ad_spend", days: int = 90
) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = await db.execute(
        select(AdInsightModel.date, AdInsightModel.spend)
        .where(AdInsightModel.organization_id == org_id, AdInsightModel.date >= since)
        .order_by(AdInsightModel.date)
    )
    values = [(row[0], float(row[1])) for row in rows.all()]
    if len(values) < 7:
        return []

    nums = [v[1] for v in values]
    mean = statistics.mean(nums)
    stdev = statistics.stdev(nums) if len(nums) > 1 else 0
    if stdev == 0:
        return []

    anomalies = []
    for date_val, val in values:
        z = (val - mean) / stdev
        if abs(z) > 2.0:
            anomalies.append(
                {
                    "date": str(date_val),
                    "value": val,
                    "z_score": round(z, 2),
                    "severity": "high" if abs(z) > 3.0 else "medium",
                    "direction": "up" if z > 0 else "down",
                }
            )
    return anomalies


# ── Simple Prediction (Linear Regression) ────────────────────────────────────


async def predict_metric(
    db: AsyncSession, org_id: UUID, metric: str = "ad_spend", periods: int = 7
) -> list[dict]:
    since = datetime.now(UTC) - timedelta(days=90)
    rows = await db.execute(
        select(AdInsightModel.date, AdInsightModel.spend)
        .where(AdInsightModel.organization_id == org_id, AdInsightModel.date >= since)
        .order_by(AdInsightModel.date)
    )
    data = [(row[0], float(row[1])) for row in rows.all()]
    if len(data) < 3:
        return []

    x_vals = list(range(len(data)))
    y_vals = [v[1] for v in data]
    n = len(x_vals)
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals, strict=False))
    sum_xx = sum(x * x for x in x_vals)
    slope = (
        (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        if (n * sum_xx - sum_x * sum_x) != 0
        else 0
    )
    intercept = (sum_y - slope * sum_x) / n

    last_date = data[-1][0]
    predictions = []
    for i in range(1, periods + 1):
        pred_date = last_date + timedelta(days=i)
        pred_val = slope * (n + i - 1) + intercept
        predictions.append(
            {
                "date": str(pred_date),
                "predicted_value": round(max(0, pred_val), 2),
            }
        )
    return predictions


# ── Dashboard Service ────────────────────────────────────────────────────────


class DashboardService:
    def __init__(
        self,
        dash_repo: DashboardRepository,
        widget_repo: DashboardWidgetRepository,
        db: AsyncSession,
    ):
        self.dash_repo = dash_repo
        self.widget_repo = widget_repo
        self.db = db

    async def create_dashboard(
        self, org_id: UUID, name: str, created_by: UUID, description: str = ""
    ) -> Dashboard:
        dash = Dashboard.create(org_id, name, created_by, description=description)
        return await self.dash_repo.save(dash)

    async def list_dashboards(self, org_id: UUID) -> list[dict]:
        dashboards = await self.dash_repo.find_by_organization(org_id)
        all_widgets = await self.widget_repo.find_by_dashboard_ids([d.id for d in dashboards])
        widgets_by_dashboard: dict[UUID, int] = {}
        for w in all_widgets:
            widgets_by_dashboard[w.dashboard_id] = widgets_by_dashboard.get(w.dashboard_id, 0) + 1
        return [
            {
                "id": str(d.id),
                "name": d.name,
                "description": d.description,
                "layout_columns": d.layout_columns,
                "is_default": d.is_default,
                "widget_count": widgets_by_dashboard.get(d.id, 0),
                "created_at": d.created_at.isoformat(),
            }
            for d in dashboards
        ]

    async def get_dashboard(self, dashboard_id: UUID) -> dict:
        dash = await self.dash_repo.find_by_id(dashboard_id)
        if dash is None:
            raise EntityNotFoundError("Dashboard", str(dashboard_id))
        widgets = await self.widget_repo.find_by_dashboard(dashboard_id)
        return {
            "id": str(dash.id),
            "name": dash.name,
            "description": dash.description,
            "layout_columns": dash.layout_columns,
            "is_default": dash.is_default,
            "created_at": dash.created_at.isoformat(),
            "widgets": [
                {
                    "id": str(w.id),
                    "widget_type": w.widget_type,
                    "title": w.title,
                    "pos_x": w.pos_x,
                    "pos_y": w.pos_y,
                    "width": w.width,
                    "height": w.height,
                    "config": w.config,
                }
                for w in widgets
            ],
        }

    async def delete_dashboard(self, dashboard_id: UUID) -> None:
        await self.widget_repo.delete_by_dashboard(dashboard_id)
        await self.dash_repo.delete(dashboard_id)

    # ── Widget management ────────────────────────────────────────────────

    async def add_widget(
        self,
        dashboard_id: UUID,
        widget_type: str,
        title: str,
        pos_x: int = 0,
        pos_y: int = 0,
        width: int = 1,
        height: int = 1,
        config: dict | None = None,
    ) -> DashboardWidget:
        dash = await self.dash_repo.find_by_id(dashboard_id)
        if dash is None:
            raise EntityNotFoundError("Dashboard", str(dashboard_id))
        widget = DashboardWidget.create(
            dashboard_id=dashboard_id,
            widget_type=widget_type,
            title=title,
            pos_x=pos_x,
            pos_y=pos_y,
            width=width,
            height=height,
            config=config,
        )
        return await self.widget_repo.save(widget)

    async def update_widget(
        self,
        widget_id: UUID,
        title: str | None = None,
        pos_x: int | None = None,
        pos_y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        config: dict | None = None,
    ) -> DashboardWidget:
        widget = await self.widget_repo.find_by_id(widget_id)
        if widget is None:
            raise EntityNotFoundError("DashboardWidget", str(widget_id))
        if title is not None:
            widget.title = title
        if pos_x is not None:
            widget.pos_x = pos_x
        if pos_y is not None:
            widget.pos_y = pos_y
        if width is not None:
            widget.width = width
        if height is not None:
            widget.height = height
        if config is not None:
            widget.config = config
        widget.updated_at = now()
        return await self.widget_repo.save(widget)

    async def delete_widget(self, widget_id: UUID) -> None:
        await self.widget_repo.delete(widget_id)

    # ── Data queries for rendering ────────────────────────────────────────

    async def query_widget_data(
        self, widget: DashboardWidget, org_id: UUID, days: int = 30
    ) -> dict:
        metric = widget.config.get("metric", "")
        return await query_metric(self.db, org_id, metric, days=days)

    async def query_dashboard_data(
        self, dashboard_id: UUID, org_id: UUID, days: int = 30
    ) -> list[dict]:
        widgets = await self.widget_repo.find_by_dashboard(dashboard_id)
        results = []
        for w in widgets:
            data = await self.query_widget_data(w, org_id, days=days)
            results.append(
                {
                    "widget_id": str(w.id),
                    "widget_type": w.widget_type,
                    "title": w.title,
                    "position": {"x": w.pos_x, "y": w.pos_y, "w": w.width, "h": w.height},
                    "config": w.config,
                    "data": data,
                }
            )
        return results

    async def get_anomalies(
        self, org_id: UUID, metric: str = "ad_spend", days: int = 90
    ) -> list[dict]:
        return await detect_anomalies(self.db, org_id, metric=metric, days=days)

    async def get_prediction(
        self, org_id: UUID, metric: str = "ad_spend", periods: int = 7
    ) -> list[dict]:
        return await predict_metric(self.db, org_id, metric=metric, periods=periods)

    async def query_single_metric(self, org_id: UUID, metric: str, days: int = 30) -> dict:
        return await query_metric(self.db, org_id, metric, days=days)
