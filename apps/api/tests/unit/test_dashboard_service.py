from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.dashboards.dashboard_service import (
    DashboardRepository,
    DashboardService,
    DashboardWidgetRepository,
    detect_anomalies,
    predict_metric,
    query_metric,
)
from app.domain.entities.dashboards.dashboard import Dashboard, DashboardWidget
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


class TestQueryMetric:
    async def test_campaigns_total(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 42
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "campaigns_total")

        assert r["value"] == 42
        assert r["metric"] == "campaigns_total"

    async def test_campaigns_total_none(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = None
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "campaigns_total")

        assert r["value"] == 0

    async def test_campaigns_active(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 5
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "campaigns_active")

        assert r["value"] == 5

    async def test_campaigns_by_status(self, mock_db):
        row1 = ("active", 3)
        row2 = ("draft", 7)
        result = MagicMock()
        result.all.return_value = [row1, row2]
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "campaigns_by_status")

        assert r["value"] == {"active": 3, "draft": 7}

    async def test_ad_spend(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 1000.50
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "ad_spend")

        assert r["value"] == 1000.50

    async def test_ad_impressions(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 50000
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "ad_impressions")

        assert r["value"] == 50000

    async def test_ad_clicks(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 1200
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "ad_clicks")

        assert r["value"] == 1200

    async def test_ad_conversions(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 50
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "ad_conversions")

        assert r["value"] == 50

    async def test_ad_ctr(self, mock_db):
        imp_result = MagicMock()
        imp_result.scalar.return_value = 1000
        clk_result = MagicMock()
        clk_result.scalar.return_value = 50
        mock_db.execute = AsyncMock(side_effect=[imp_result, clk_result])

        r = await query_metric(mock_db, uuid4(), "ad_ctr")

        assert r["value"] == 5.0

    async def test_ad_ctr_zero_impressions(self, mock_db):
        imp_result = MagicMock()
        imp_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=imp_result)

        r = await query_metric(mock_db, uuid4(), "ad_ctr")

        assert r["value"] == 0.0

    async def test_ad_spend_trend(self, mock_db):
        row1 = ("2025-01-01", 100.0)
        row2 = ("2025-01-02", 150.0)
        result = MagicMock()
        result.all.return_value = [row1, row2]
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "ad_spend_trend")

        assert len(r["value"]) == 2
        assert r["value"][0]["date"] == "2025-01-01"
        assert r["value"][0]["value"] == 100.0

    async def test_content_published(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 15
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "content_published")

        assert r["value"] == 15

    async def test_content_by_type(self, mock_db):
        row1 = ("blog", 5)
        row2 = ("social", 3)
        result = MagicMock()
        result.all.return_value = [row1, row2]
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "content_by_type")

        assert r["value"] == {"blog": 5, "social": 3}

    async def test_email_sent(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 10000
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "email_sent")

        assert r["value"] == 10000

    async def test_email_open_rate(self, mock_db):
        sent_result = MagicMock()
        sent_result.scalar.return_value = 1000
        open_result = MagicMock()
        open_result.scalar.return_value = 250
        mock_db.execute = AsyncMock(side_effect=[sent_result, open_result])

        r = await query_metric(mock_db, uuid4(), "email_open_rate")

        assert r["value"] == 25.0

    async def test_email_open_rate_zero_sent(self, mock_db):
        sent_result = MagicMock()
        sent_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=sent_result)

        r = await query_metric(mock_db, uuid4(), "email_open_rate")

        assert r["value"] == 0.0

    async def test_email_campaigns(self, mock_db):
        result = MagicMock()
        result.scalar.return_value = 8
        mock_db.execute.return_value = result

        r = await query_metric(mock_db, uuid4(), "email_campaigns")

        assert r["value"] == 8

    async def test_unknown_metric(self, mock_db):
        r = await query_metric(mock_db, uuid4(), "unknown_metric")

        assert r["value"] == 0
        assert r["metric"] == "unknown_metric"


class TestDetectAnomalies:
    async def test_no_anomalies(self, mock_db):
        result = MagicMock()
        result.all.return_value = [
            ("2025-01-01", 100.0),
            ("2025-01-02", 102.0),
            ("2025-01-03", 98.0),
            ("2025-01-04", 101.0),
            ("2025-01-05", 99.0),
            ("2025-01-06", 100.0),
            ("2025-01-07", 101.0),
        ]
        mock_db.execute.return_value = result

        anomalies = await detect_anomalies(mock_db, uuid4())

        assert anomalies == []

    async def test_detects_anomaly(self, mock_db):
        result = MagicMock()
        result.all.return_value = [
            ("2025-01-01", 100.0),
            ("2025-01-02", 102.0),
            ("2025-01-03", 98.0),
            ("2025-01-04", 101.0),
            ("2025-01-05", 99.0),
            ("2025-01-06", 100.0),
            ("2025-01-07", 1000.0),
        ]
        mock_db.execute.return_value = result

        anomalies = await detect_anomalies(mock_db, uuid4())

        assert len(anomalies) >= 1
        assert anomalies[0]["date"] == "2025-01-07"

    async def test_insufficient_data(self, mock_db):
        result = MagicMock()
        result.all.return_value = [("2025-01-01", 100.0)]
        mock_db.execute.return_value = result

        anomalies = await detect_anomalies(mock_db, uuid4())

        assert anomalies == []

    async def test_zero_stdev(self, mock_db):
        result = MagicMock()
        result.all.return_value = [
            ("2025-01-01", 100.0),
            ("2025-01-02", 100.0),
            ("2025-01-03", 100.0),
            ("2025-01-04", 100.0),
            ("2025-01-05", 100.0),
            ("2025-01-06", 100.0),
            ("2025-01-07", 100.0),
        ]
        mock_db.execute.return_value = result

        anomalies = await detect_anomalies(mock_db, uuid4())

        assert anomalies == []


class TestPredictMetric:
    async def test_returns_predictions(self, mock_db):
        rows = [(datetime(2025, 1, d), 100.0) for d in range(1, 11)]
        result = MagicMock()
        result.all.return_value = rows
        mock_db.execute.return_value = result

        predictions = await predict_metric(mock_db, uuid4(), periods=3)

        assert len(predictions) == 3
        assert "date" in predictions[0]
        assert "predicted_value" in predictions[0]
        assert predictions[0]["predicted_value"] >= 0

    async def test_insufficient_data(self, mock_db):
        result = MagicMock()
        result.all.return_value = [("2025-01-01", 100.0)]
        mock_db.execute.return_value = result

        predictions = await predict_metric(mock_db, uuid4())

        assert predictions == []


class TestDashboardService:
    @pytest.fixture
    def dash_repo(self):
        return MagicMock(spec=DashboardRepository)

    @pytest.fixture
    def widget_repo(self):
        return MagicMock(spec=DashboardWidgetRepository)

    @pytest.fixture
    def service(self, dash_repo, widget_repo, mock_db):
        return DashboardService(dash_repo=dash_repo, widget_repo=widget_repo, db=mock_db)

    async def test_create_dashboard(self, service, dash_repo):
        org_id = uuid4()
        user_id = uuid4()
        expected = Dashboard(id=uuid4(), name="Test", organization_id=org_id)
        dash_repo.save = AsyncMock(return_value=expected)

        result = await service.create_dashboard(org_id, "Test", user_id)

        assert result.name == "Test"
        dash_repo.save.assert_awaited_once()

    async def test_list_dashboards(self, service, dash_repo, widget_repo):
        dash_id = uuid4()
        dash = Dashboard(
            id=dash_id, name="Test", description="desc", layout_columns=3, is_default=True
        )
        dash_repo.find_by_organization = AsyncMock(return_value=[dash])
        widget_repo.find_by_dashboard_ids = AsyncMock(
            return_value=[
                DashboardWidget(
                    id=uuid4(), dashboard_id=dash_id, widget_type="kpi_card", title="Spend"
                ),
            ]
        )

        result = await service.list_dashboards(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Test"
        assert result[0]["widget_count"] == 1

    async def test_get_dashboard(self, service, dash_repo, widget_repo):
        dash_id = uuid4()
        dash = Dashboard(id=dash_id, name="My Dashboard")
        dash_repo.find_by_id = AsyncMock(return_value=dash)
        widget_repo.find_by_dashboard = AsyncMock(return_value=[])

        result = await service.get_dashboard(dash_id)

        assert result["name"] == "My Dashboard"
        assert result["widgets"] == []

    async def test_get_dashboard_not_found(self, service, dash_repo):
        dash_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.get_dashboard(uuid4())

    async def test_delete_dashboard(self, service, dash_repo, widget_repo):
        dash_id = uuid4()
        dash_repo.delete = AsyncMock()
        widget_repo.delete_by_dashboard = AsyncMock()

        await service.delete_dashboard(dash_id)

        widget_repo.delete_by_dashboard.assert_awaited_with(dash_id)
        dash_repo.delete.assert_awaited_with(dash_id)

    async def test_add_widget(self, service, dash_repo, widget_repo):
        dash_id = uuid4()
        dash_repo.find_by_id = AsyncMock(return_value=Dashboard(id=dash_id, name="Dash"))
        widget_repo.save = AsyncMock(
            return_value=DashboardWidget(
                id=uuid4(),
                dashboard_id=dash_id,
                widget_type="kpi_card",
                title="Spend",
            )
        )

        result = await service.add_widget(dash_id, "kpi_card", "Spend")

        assert result.widget_type == "kpi_card"
        assert result.title == "Spend"

    async def test_add_widget_dashboard_not_found(self, service, dash_repo):
        dash_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.add_widget(uuid4(), "metric", "Spend")

    async def test_update_widget(self, service, widget_repo):
        widget_id = uuid4()
        widget = DashboardWidget(id=widget_id, widget_type="kpi_card", title="Old")
        widget_repo.find_by_id = AsyncMock(return_value=widget)
        widget_repo.save = AsyncMock(side_effect=lambda w: w)

        result = await service.update_widget(widget_id, title="New Title", pos_x=2, pos_y=3)

        assert result.title == "New Title"
        assert result.pos_x == 2
        assert result.pos_y == 3

    async def test_update_widget_not_found(self, service, widget_repo):
        widget_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(EntityNotFoundError):
            await service.update_widget(uuid4(), title="New")

    async def test_delete_widget(self, service, widget_repo):
        widget_id = uuid4()
        widget_repo.delete = AsyncMock()

        await service.delete_widget(widget_id)

        widget_repo.delete.assert_awaited_with(widget_id)

    async def test_query_single_metric(self, service, mock_db):
        result = MagicMock()
        result.scalar.return_value = 42
        mock_db.execute.return_value = result

        r = await service.query_single_metric(uuid4(), "campaigns_total")

        assert r["value"] == 42
