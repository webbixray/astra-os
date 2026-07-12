"""Tests for Observability Services — E6.4 Beta Launch."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.entities.observability import (
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AlertSource,
    Budget,
    BudgetCategory,
    CostRecord,
    Dashboard,
    DashboardWidget,
    DashboardWidgetType,
    MetricDefinition,
    MetricSample,
    MetricType,
    SLADefinition,
    SLAReport,
    SLAType,
)


class TestMetricDefinition:
    def test_create_metric_definition(self):
        metric = MetricDefinition(
            organization_id=uuid4(),
            name="api_latency",
            display_name="API Latency",
            description="End-to-end API latency",
            metric_type=MetricType.HISTOGRAM,
            unit="ms",
            label_names=["endpoint", "method", "status"],
            collection_interval_seconds=30,
            retention_days=60,
            alert_thresholds={"warning": 200, "critical": 1000},
        )
        assert metric.name == "api_latency"
        assert metric.metric_type == MetricType.HISTOGRAM
        assert metric.unit == "ms"
        assert "endpoint" in metric.label_names

    def test_to_dict(self):
        metric = MetricDefinition(
            organization_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            metric_type=MetricType.GAUGE,
        )
        d = metric.to_dict()
        assert d["name"] == "test_metric"
        assert d["metric_type"] == "gauge"
        assert "id" in d


class TestMetricSample:
    def test_create_metric_sample(self):
        metric_id = uuid4()
        sample = MetricSample(
            metric_id=metric_id,
            organization_id=uuid4(),
            value=150.5,
            labels={"endpoint": "/api/users", "method": "GET", "status": "200"},
        )
        assert sample.value == 150.5
        assert sample.labels["endpoint"] == "/api/users"

    def test_to_dict(self):
        sample = MetricSample(
            metric_id=uuid4(),
            organization_id=uuid4(),
            value=100.0,
        )
        d = sample.to_dict()
        assert d["value"] == 100.0


class TestAlertRule:
    def test_create_alert_rule(self):
        rule = AlertRule(
            organization_id=uuid4(),
            name="High Latency Alert",
            description="Alert when API latency exceeds threshold",
            source=AlertSource.APPLICATION,
            severity=AlertSeverity.WARNING,
            metric_name="api_latency",
            condition="avg > 500",
            evaluation_window_seconds=300,
            label_matchers={"endpoint": "/api/*"},
            notification_channels=["slack", "email"],
            auto_resolve=True,
        )
        assert rule.name == "High Latency Alert"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.condition == "avg > 500"

    def test_to_dict(self):
        rule = AlertRule(
            organization_id=uuid4(),
            name="Test Alert",
            metric_name="test",
            condition="> 100",
        )
        d = rule.to_dict()
        assert d["name"] == "Test Alert"
        assert "id" in d


class TestAlert:
    def test_create_alert(self):
        alert = Alert(
            organization_id=uuid4(),
            alert_rule_id=uuid4(),
            status=AlertStatus.FIRING,
            severity=AlertSeverity.CRITICAL,
            title="High Latency",
            description="API latency exceeded threshold",
            metric_name="api_latency",
            metric_value=1200.0,
            threshold_value=1000.0,
            labels={"endpoint": "/api/users"},
            fingerprint="abc123",
        )
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.FIRING

    def test_is_active(self):
        firing = Alert(status=AlertStatus.FIRING)
        acknowledged = Alert(status=AlertStatus.ACKNOWLEDGED)
        resolved = Alert(status=AlertStatus.RESOLVED)

        assert firing.is_active() is True
        assert acknowledged.is_active() is True
        assert resolved.is_active() is False

    def test_duration_seconds(self):
        started = datetime.now() - timedelta(seconds=300)
        alert = Alert(started_at=started)
        duration = alert.duration_seconds()
        assert 290 < duration < 310

    def test_to_dict(self):
        alert = Alert(
            organization_id=uuid4(),
            alert_rule_id=uuid4(),
            title="Test Alert",
        )
        d = alert.to_dict()
        assert d["title"] == "Test Alert"
        assert "id" in d


class TestCostRecord:
    def test_create_cost_record(self):
        record = CostRecord(
            organization_id=uuid4(),
            category=BudgetCategory.AI_INFERENCE,
            amount_usd=150.50,
            resource_type="tokens",
            resource_id="gpt-4",
            quantity=1_000_000,
            unit="tokens",
            unit_cost_usd=0.00015,
            provider="openai",
        )
        assert record.category == BudgetCategory.AI_INFERENCE
        assert record.amount_usd == 150.50

    def test_to_dict(self):
        record = CostRecord(organization_id=uuid4(), category=BudgetCategory.COMPUTE, amount_usd=100.0)
        d = record.to_dict()
        assert d["amount_usd"] == 100.0
        assert d["category"] == "compute"


class TestBudget:
    def test_create_budget(self):
        budget = Budget(
            organization_id=uuid4(),
            name="Monthly AI Budget",
            amount_usd=10000.0,
            period="monthly",
            category=BudgetCategory.AI_INFERENCE,
            warning_threshold_pct=0.8,
            critical_threshold_pct=0.95,
        )
        assert budget.name == "Monthly AI Budget"
        assert budget.amount_usd == 10000.0

    def test_is_over_warning(self):
        budget = Budget(amount_usd=1000.0, warning_threshold_pct=0.8)
        budget.current_spend_usd = 850.0
        assert budget.is_over_warning() is True

        budget.current_spend_usd = 700.0
        assert budget.is_over_warning() is False

    def test_is_over_critical(self):
        budget = Budget(amount_usd=1000.0, critical_threshold_pct=0.95)
        budget.current_spend_usd = 960.0
        assert budget.is_over_critical() is True

    def test_is_exhausted(self):
        budget = Budget(amount_usd=1000.0)
        budget.current_spend_usd = 1000.0
        assert budget.is_exhausted() is True

        budget.current_spend_usd = 999.0
        assert budget.is_exhausted() is False

    def test_to_dict(self):
        budget = Budget(organization_id=uuid4(), name="Test", amount_usd=500.0)
        d = budget.to_dict()
        assert d["name"] == "Test"
        assert d["amount_usd"] == 500.0


class TestSLADefinition:
    def test_create_sla(self):
        sla = SLADefinition(
            organization_id=uuid4(),
            name="API Availability SLA",
            sla_type=SLAType.AVAILABILITY,
            target_value=99.9,
            target_unit="%",
            service_name="api-gateway",
            measurement_window="monthly",
        )
        assert sla.sla_type == SLAType.AVAILABILITY
        assert sla.target_value == 99.9

    def test_to_dict(self):
        sla = SLADefinition(organization_id=uuid4(), name="Test SLA", sla_type=SLAType.LATENCY)
        d = sla.to_dict()
        assert d["name"] == "Test SLA"
        assert d["sla_type"] == "latency"


class TestSLAReport:
    def test_to_dict(self):
        report = SLAReport(
            organization_id=uuid4(),
            sla_definition_id=uuid4(),
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            measured_value=99.95,
            target_value=99.9,
            unit="%",
            is_compliant=True,
        )
        d = report.to_dict()
        assert d["is_compliant"] is True
        assert d["measured_value"] == 99.95


class TestDashboard:
    def test_create_dashboard(self):
        dashboard = Dashboard(
            organization_id=uuid4(),
            name="Marketing Dashboard",
            description="Campaign performance overview",
            created_by=uuid4(),
        )
        assert dashboard.name == "Marketing Dashboard"

    def test_to_dict(self):
        dashboard = Dashboard(organization_id=uuid4(), name="Test")
        d = dashboard.to_dict()
        assert d["name"] == "Test"


class TestDashboardWidget:
    def test_create_widget(self):
        widget = DashboardWidget(
            dashboard_id=uuid4(),
            widget_type=DashboardWidgetType.LINE_CHART,
            title="API Latency Over Time",
            metric_names=["api_latency"],
            visualization_config={"color": "blue", "line_width": 2},
            position_x=0,
            position_y=0,
            width=6,
            height=4,
        )
        assert widget.widget_type == DashboardWidgetType.LINE_CHART

    def test_to_dict(self):
        widget = DashboardWidget(dashboard_id=uuid4(), title="Test")
        d = widget.to_dict()
        assert d["title"] == "Test"


class TestAlertRule:
    def test_create_with_all_fields(self):
        rule = AlertRule(
            organization_id=uuid4(),
            name="Test Alert",
            metric_name="cpu_usage",
            condition="avg > 80",
            evaluation_window_seconds=300,
            label_matchers={"host": "prod-*"},
            notification_channels=["slack", "pagerduty"],
            auto_resolve=True,
            group_by=["host"],
        )
        assert rule.notification_channels == ["slack", "pagerduty"]
        assert rule.group_by == ["host"]


class TestAlert:
    def test_fingerprint_generation(self):
        alert = Alert(
            metric_name="cpu",
            labels={"host": "server-1"},
            fingerprint="cpu:server-1",
        )
        assert alert.fingerprint == "cpu:server-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])