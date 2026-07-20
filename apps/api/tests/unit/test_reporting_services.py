import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.reports.enhanced_reporting_service import (
    EnhancedReportingService,
)
from app.application.use_cases.reports.reporting_service import ReportingService
from app.domain.entities.reports.report_template import ReportTemplate
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ValidationError,
)


@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


class TestReportingService:
    @pytest.fixture
    def service(self, mock_db):
        return ReportingService(session=mock_db)

    async def test_get_trends(self, service, mock_db):
        row1 = MagicMock(date="2025-01-01", value=100.0)
        row2 = MagicMock(date="2025-01-02", value=150.0)
        result = MagicMock()
        result.all.return_value = [row1, row2]
        mock_db.execute.return_value = result

        with patch("app.application.use_cases.reports.reporting_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_dt
            mock_dt.date.return_value = date(2025, 1, 3)
            trends = await service.get_trends(uuid4(), metric="spend", days=2)

        assert trends["metric"] == "spend"
        assert trends["total"] == 250.0
        assert len(trends["daily"]) == 3

    async def test_get_trends_empty(self, service, mock_db):
        result = MagicMock()
        result.all.return_value = []
        mock_db.execute.return_value = result

        trends = await service.get_trends(uuid4(), days=7)

        assert trends["total"] == 0
        assert trends["peak"] == 0

    async def test_get_campaign_timeline(self, service, mock_db):
        ins1 = MagicMock(
            ad_campaign_id=uuid4(),
            date="2025-01-01",
            impressions=100,
            clicks=5,
            spend=50.0,
            conversions=2,
            revenue=200.0,
        )
        ins2 = MagicMock(
            ad_campaign_id=ins1.ad_campaign_id,
            date="2025-01-02",
            impressions=200,
            clicks=10,
            spend=100.0,
            conversions=4,
            revenue=400.0,
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [ins1, ins2]
        mock_db.execute.return_value = result

        timeline = await service.get_campaign_timeline(
            uuid4(), [uuid4()], "2025-01-01", "2025-01-31"
        )

        assert len(timeline) == 1
        assert len(timeline[0]["data"]) == 2

    async def test_get_platform_comparison(self, service, mock_db):
        row = MagicMock(
            platform="google",
            impressions=10000,
            clicks=500,
            spend=1000.0,
            conversions=50,
            revenue=5000.0,
        )
        result = MagicMock()
        result.all.return_value = [row]
        mock_db.execute.return_value = result

        comp = await service.get_platform_comparison(uuid4())

        assert len(comp["platforms"]) == 1
        assert comp["platforms"][0]["ctr"] == 5.0
        assert comp["platforms"][0]["cpc"] == 2.0
        assert comp["platforms"][0]["roas"] == 5.0

    async def test_export_csv_campaigns(self, service, mock_db):
        c = MagicMock(
            id=uuid4(),
            name="Test Campaign",
            status="active",
            budget_amount=1000.0,
            start_date=MagicMock(isoformat=lambda: "2025-01-01"),
            end_date=MagicMock(isoformat=lambda: "2025-02-01"),
            channels=["social", "search"],
            objective="awareness",
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [c]
        mock_db.execute.return_value = result

        csv_output = await service.export_csv("campaigns", uuid4())

        assert "Test Campaign" in csv_output
        assert "active" in csv_output
        assert "social, search" in csv_output

    async def test_export_csv_content(self, service, mock_db):
        c = MagicMock(
            id=uuid4(),
            title="Blog Post",
            content_type="blog",
            status="published",
            version=1,
            created_at=MagicMock(isoformat=lambda: "2025-01-01T00:00:00"),
            scheduled_at=MagicMock(isoformat=lambda: "2025-01-15T00:00:00"),
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [c]
        mock_db.execute.return_value = result

        csv_output = await service.export_csv("content", uuid4())

        assert "Blog Post" in csv_output
        assert "published" in csv_output

    async def test_export_csv_ads(self, service, mock_db):
        ins = MagicMock(
            date="2025-01-01",
            platform="google",
            ad_campaign_id=uuid4(),
            impressions=1000,
            clicks=50,
            spend=100.0,
            conversions=5,
            revenue=500.0,
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [ins]
        mock_db.execute.return_value = result

        csv_output = await service.export_csv("ads", uuid4())

        assert "google" in csv_output
        assert "1000" in csv_output

    async def test_export_csv_ad_accounts(self, service, mock_db):
        with patch.dict(
            "sys.modules",
            {
                "app.infrastructure.db.models.advertising.advertising_models": MagicMock(
                    AdAccountModel=MagicMock(
                        organization_id=uuid4,
                    )
                )
            },
        ):
            pass

        a = MagicMock(
            id=uuid4(),
            platform="google",
            account_name="My Account",
            status="connected",
            last_synced_at=MagicMock(isoformat=lambda: "2025-01-01T00:00:00"),
            organization_id=uuid4,
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [a]
        mock_db.execute.return_value = result

        csv_output = await service.export_csv("ad_accounts", uuid4())

        assert "My Account" in csv_output
        assert "connected" in csv_output


class TestEnhancedReportingService:
    @pytest.fixture
    def service(self, mock_db):
        return EnhancedReportingService(session=mock_db)

    async def test_create_template(self, service):
        template_repo = MagicMock()
        template_repo.save = AsyncMock(
            return_value=ReportTemplate(
                id=uuid4(),
                name="Weekly Report",
                report_type="campaigns",
            )
        )
        service.template_repo = template_repo

        result = await service.create_template(uuid4(), "Weekly Report", "campaigns")

        assert result.name == "Weekly Report"

    async def test_list_templates(self, service):
        template_repo = MagicMock()
        t = ReportTemplate(id=uuid4(), name="Monthly", report_type="ads")
        template_repo.find_by_organization = AsyncMock(return_value=[t])
        service.template_repo = template_repo

        result = await service.list_templates(uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Monthly"

    async def test_get_template(self, service):
        template_id = uuid4()
        template_repo = MagicMock()
        template_repo.find_by_id = AsyncMock(
            return_value=ReportTemplate(
                id=template_id,
                name="Template",
                report_type="ads",
            )
        )
        service.template_repo = template_repo

        result = await service.get_template(template_id)

        assert result.name == "Template"

    async def test_get_template_not_found(self, service):
        template_repo = MagicMock()
        template_repo.find_by_id = AsyncMock(return_value=None)
        service.template_repo = template_repo

        with pytest.raises(EntityNotFoundError):
            await service.get_template(uuid4())

    async def test_update_template(self, service):
        template_id = uuid4()
        t = ReportTemplate(id=template_id, name="Old", report_type="campaigns")
        template_repo = MagicMock()
        template_repo.find_by_id = AsyncMock(return_value=t)
        template_repo.save = AsyncMock(side_effect=lambda t: t)
        service.template_repo = template_repo

        result = await service.update_template(template_id, name="New Name")

        assert result.name == "New Name"

    async def test_delete_template(self, service):
        template_repo = MagicMock()
        template_repo.delete = AsyncMock()
        service.template_repo = template_repo

        await service.delete_template(uuid4())

        template_repo.delete.assert_awaited_once()

    async def test_generate_report_csv(self, service, mock_db):
        with patch.object(service, "_fetch_report_data", AsyncMock(return_value={"total": 10})):
            report = await service.generate_report(uuid4(), "campaigns", format="csv", days=30)

        assert "campaigns_report" in report
        assert "10" in report

    async def test_generate_report_json(self, service, mock_db):
        data = {"impressions": 1000, "clicks": 50, "spend": 100.0}
        with patch.object(service, "_fetch_report_data", AsyncMock(return_value=data)):
            report = await service.generate_report(uuid4(), "ads", format="json", days=30)

        parsed = json.loads(report)
        assert parsed["impressions"] == 1000

    async def test_generate_report_html(self, service, mock_db):
        data = {"total": 10, "active": 5}
        with patch.object(service, "_fetch_report_data", AsyncMock(return_value=data)):
            report = await service.generate_report(uuid4(), "overview", format="html", days=30)

        assert "<html>" in report
        assert "10" in report

    async def test_generate_report_invalid_format(self, service):
        with pytest.raises(ValidationError):
            await service.generate_report(uuid4(), "campaigns", format="pdf")

    async def test_generate_and_deliver_success(self, service, mock_db):
        delivery_repo = MagicMock()
        delivery_repo.save = AsyncMock(return_value=MagicMock(status="success"))
        service.delivery_repo = delivery_repo

        with (
            patch.object(service, "_fetch_report_data", AsyncMock(return_value={"total": 0})),
            patch(
                "app.application.use_cases.reports.enhanced_reporting_service.get_delivery_adapter"
            ) as mock_get_adapter,
        ):
            adapter = MagicMock()
            adapter.deliver = AsyncMock(return_value=True)
            mock_get_adapter.return_value = adapter

            log = await service.generate_and_deliver(
                uuid4(),
                "overview",
                channel="email",
                recipient="admin@test.com",
                format="csv",
            )

            assert log.status == "success"

    async def test_generate_and_deliver_failure(self, service, mock_db):
        with (
            patch.object(service, "_fetch_report_data", AsyncMock(return_value={"total": 0})),
            patch(
                "app.application.use_cases.reports.enhanced_reporting_service.get_delivery_adapter"
            ) as mock_get_adapter,
        ):
            adapter = MagicMock()
            adapter.deliver = AsyncMock(side_effect=Exception("SMTP error"))
            mock_get_adapter.return_value = adapter

            log = await service.generate_and_deliver(
                uuid4(),
                "overview",
                channel="email",
                recipient="admin@test.com",
            )

            assert "SMTP error" in str(log.error_message)

    async def test_compare_periods(self, service, mock_db):
        with patch.object(service, "_fetch_report_data", AsyncMock(return_value={"total": 5})):
            comparison = await service.compare_periods(uuid4(), "campaigns", current_days=7)

        assert comparison["report_type"] == "campaigns"
        assert comparison["comparison_type"] == "previous_period"
        assert "comparison" in comparison

    async def test_get_delivery_logs(self, service):
        delivery_repo = MagicMock()
        log = MagicMock(
            id=uuid4(),
            report_type="campaigns",
            format="csv",
            channel="email",
            recipient="admin@test.com",
            status="success",
            error_message=None,
            generated_at=MagicMock(isoformat=lambda: "2025-01-01T00:00:00"),
        )
        delivery_repo.find_by_organization = AsyncMock(return_value=[log])
        service.delivery_repo = delivery_repo

        logs = await service.get_delivery_logs(uuid4())

        assert len(logs) == 1
        assert logs[0]["status"] == "success"

    def test_summarize(self, service):
        data = {"total": 10, "active": 5, "campaigns": [1, 2, 3]}
        summary = service._summarize(data)

        assert summary["total"] == 10.0
        assert summary["campaigns_count"] == 3.0

    def test_to_csv(self, service):
        data = {"total": 10, "active": 5}
        csv_out = service._to_csv(data, "test_report")

        assert "test_report" in csv_out
        assert "10" in csv_out

    def test_to_csv_with_nested(self, service):
        data = {"campaigns": [{"name": "Campaign A", "status": "active"}]}
        csv_out = service._to_csv(data, "campaigns")

        assert "Campaign A" in csv_out

    def test_to_html(self, service):
        data = {"total": 10, "active": 5}
        html = service._to_html(data, "test_report")

        assert "<html>" in html
        assert "Test Report" in html
        assert "10" in html

    def test_to_html_with_nested_dict(self, service):
        data = {"campaigns": {"total": 5, "active": 3}}
        html = service._to_html(data, "campaigns")

        assert "<table>" in html
