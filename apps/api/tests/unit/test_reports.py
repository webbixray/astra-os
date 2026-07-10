from uuid import uuid4

import pytest

from app.domain.entities.reports.report_schedule import ReportSchedule
from app.domain.entities.reports.report_template import (
    COMPARISON_PERIODS,
    EXPORT_FORMATS,
    REPORT_TYPES,
    ReportDeliveryLog,
    ReportTemplate,
)
from app.domain.exceptions.domain_exceptions import ValidationError


class TestReportTemplate:
    def test_create_valid_template(self):
        org_id = uuid4()
        user_id = uuid4()
        t = ReportTemplate.create(
            organization_id=org_id,
            name="Weekly Overview",
            report_type="overview",
            config={"period": "7d"},
            description="Weekly summary",
            created_by=user_id,
        )
        assert t.organization_id == org_id
        assert t.name == "Weekly Overview"
        assert t.report_type == "overview"
        assert t.config == {"period": "7d"}
        assert t.description == "Weekly summary"
        assert t.created_by == user_id

    def test_create_name_whitespace_stripped(self):
        t = ReportTemplate.create(
            organization_id=uuid4(),
            name="  Spaced  ",
            report_type="campaigns",
            created_by=uuid4(),
        )
        assert t.name == "Spaced"

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError, match="Template name is required"):
            ReportTemplate.create(organization_id=uuid4(), name="", report_type="overview")
        with pytest.raises(ValidationError, match="Template name is required"):
            ReportTemplate.create(organization_id=uuid4(), name="   ", report_type="overview")

    def test_invalid_report_type_raises(self):
        with pytest.raises(ValidationError, match="Invalid report type"):
            ReportTemplate.create(organization_id=uuid4(), name="X", report_type="not_a_type")

    def test_update_config_merges(self):
        t = ReportTemplate.create(
            organization_id=uuid4(),
            name="X",
            report_type="overview",
            config={"existing": "value"},
        )
        t.update_config({"new": "value", "existing": "overwritten"})
        assert t.config == {"existing": "overwritten", "new": "value"}

    def test_update_config_empty_preserves(self):
        t = ReportTemplate.create(
            organization_id=uuid4(),
            name="X",
            report_type="overview",
            config={"a": 1},
        )
        t.update_config({})
        assert t.config == {"a": 1}


class TestReportDeliveryLog:
    def test_create_valid_log(self):
        org_id = uuid4()
        log = ReportDeliveryLog.create(
            organization_id=org_id,
            report_type="campaigns",
            channel="email",
            format="csv",
            recipient="user@example.com",
            template_id=uuid4(),
            schedule_id=uuid4(),
        )
        assert log.organization_id == org_id
        assert log.report_type == "campaigns"
        assert log.channel == "email"
        assert log.format == "csv"
        assert log.recipient == "user@example.com"
        assert log.status == "pending"
        assert log.file_url == ""
        assert log.error_message == ""

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="Invalid export format"):
            ReportDeliveryLog.create(
                organization_id=uuid4(),
                report_type="overview",
                format="pdf",
            )

    def test_mark_success(self):
        log = ReportDeliveryLog.create(
            organization_id=uuid4(),
            report_type="overview",
            format="csv",
        )
        log.mark_success("https://example.com/report.csv")
        assert log.status == "delivered"
        assert log.file_url == "https://example.com/report.csv"

    def test_mark_failed(self):
        log = ReportDeliveryLog.create(
            organization_id=uuid4(),
            report_type="overview",
            format="csv",
        )
        log.mark_failed("SMTP timeout")
        assert log.status == "failed"
        assert log.error_message == "SMTP timeout"


class TestReportSchedule:
    def test_create_valid_schedule(self):
        org_id = uuid4()
        s = ReportSchedule.create(
            organization_id=org_id,
            name="Weekly Report",
            report_type="campaigns",
            frequency="weekly",
            recipients=["a@b.com", "c@d.com"],
            config={"filter": "active"},
            created_by=uuid4(),
        )
        assert s.organization_id == org_id
        assert s.name == "Weekly Report"
        assert s.report_type == "campaigns"
        assert s.frequency == "weekly"
        assert s.recipients == ["a@b.com", "c@d.com"]
        assert s.config == {"filter": "active"}
        assert s.is_active is True

    def test_defaults(self):
        s = ReportSchedule.create(organization_id=uuid4(), name="X")
        assert s.report_type == "overview"
        assert s.frequency == "weekly"
        assert s.recipients == []
        assert s.config == {}
        assert s.is_active is True


class TestReportConstants:
    def test_report_types(self):
        assert "overview" in REPORT_TYPES
        assert "campaigns" in REPORT_TYPES
        assert "ads" in REPORT_TYPES
        assert "content" in REPORT_TYPES
        assert "email" in REPORT_TYPES
        assert "platform_comparison" in REPORT_TYPES
        assert "custom" in REPORT_TYPES
        assert len(REPORT_TYPES) == 7

    def test_export_formats(self):
        assert EXPORT_FORMATS == ["csv", "json", "html"]

    def test_comparison_periods(self):
        assert COMPARISON_PERIODS == ["previous_period", "same_period_last_year", "custom"]
