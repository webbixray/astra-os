"""Observability Services — E6.4 Beta Launch.

Services for metrics collection, alerting, cost tracking, SLA monitoring, and dashboards.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.entities.observability import (
    Alert,
    AlertRule,
    AlertStatus,
    Budget,
    CostRecord,
    Dashboard,
    DashboardWidget,
    MetricDefinition,
    MetricSample,
    SLADefinition,
    SLAReport,
)

logger = logging.getLogger(__name__)


# --- Repository Interfaces ---

class MetricDefinitionRepository:
    async def save(self, metric: MetricDefinition) -> MetricDefinition: ...
    async def find_by_id(self, metric_id: UUID) -> MetricDefinition | None: ...
    async def find_by_organization(self, org_id: UUID, active_only: bool = True) -> list[MetricDefinition]: ...
    async def find_by_name(self, org_id: UUID, name: str) -> MetricDefinition | None: ...


class MetricSampleRepository:
    async def save_batch(self, samples: list[MetricSample]) -> list[MetricSample]: ...
    async def find_by_metric(
        self,
        metric_id: UUID,
        start: datetime,
        end: datetime,
        labels: dict[str, str] | None = None,
    ) -> list[MetricSample]: ...
    async def aggregate(
        self,
        metric_id: UUID,
        start: datetime,
        end: datetime,
        aggregation: str,  # sum, avg, min, max, count, percentile
        labels: dict[str, str] | None = None,
    ) -> float: ...


class AlertRuleRepository:
    async def save(self, rule: AlertRule) -> AlertRule: ...
    async def find_by_id(self, rule_id: UUID) -> AlertRule | None: ...
    async def find_by_organization(self, org_id: UUID, active_only: bool = True) -> list[AlertRule]: ...
    async def find_for_evaluation(self, now: datetime) -> list[AlertRule]: ...


class AlertRepository:
    async def save(self, alert: Alert) -> Alert: ...
    async def find_by_id(self, alert_id: UUID) -> Alert | None: ...
    async def find_by_organization(
        self,
        org_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[Alert]: ...
    async def find_by_fingerprint(self, fingerprint: str) -> Alert | None: ...
    async def find_active_by_org(self, org_id: UUID) -> list[Alert]: ...


class CostRecordRepository:
    async def save(self, record: CostRecord) -> CostRecord: ...
    async def find_by_organization(
        self,
        org_id: UUID,
        start: datetime,
        end: datetime,
        category: str | None = None,
    ) -> list[CostRecord]: ...
    async def get_monthly_total(self, org_id: UUID, year: int, month: int) -> float: ...


class BudgetRepository:
    async def save(self, budget: Budget) -> Budget: ...
    async def find_by_id(self, budget_id: UUID) -> Budget | None: ...
    async def find_by_organization(self, org_id: UUID, active_only: bool = True) -> list[Budget]: ...
    async def find_by_scope(self, org_id: UUID, project_id: UUID | None, campaign_id: UUID | None) -> list[Budget]: ...


class SLARepository:
    async def save(self, sla: SLADefinition) -> SLADefinition: ...
    async def find_by_id(self, sla_id: UUID) -> SLADefinition | None: ...
    async def find_by_organization(self, org_id: UUID, active_only: bool = True) -> list[SLADefinition]: ...


class SLAReportRepository:
    async def save(self, report: SLAReport) -> SLAReport: ...
    async def find_by_sla(
        self,
        sla_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[SLAReport]: ...


class DashboardRepository:
    async def save(self, dashboard: Dashboard) -> Dashboard: ...
    async def find_by_id(self, dashboard_id: UUID) -> Dashboard | None: ...
    async def find_by_organization(self, org_id: UUID) -> list[Dashboard]: ...
    async def find_default(self, org_id: UUID) -> Dashboard | None: ...


class DashboardWidgetRepository:
    async def save(self, widget: DashboardWidget) -> DashboardWidget: ...
    async def find_by_id(self, widget_id: UUID) -> DashboardWidget | None: ...
    async def find_by_dashboard(self, dashboard_id: UUID) -> list[DashboardWidget]: ...


# --- Services ---

class MetricsService:
    """Service for collecting, storing, and querying metrics."""

    def __init__(
        self,
        definition_repo: MetricDefinitionRepository,
        sample_repo: MetricSampleRepository,
        alert_rule_repo: AlertRuleRepository,
    ) -> None:
        self.definition_repo = definition_repo
        self.sample_repo = sample_repo
        self.alert_rule_repo = alert_rule_repo

    async def record_metric(
        self,
        organization_id: UUID,
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> MetricSample:
        """Record a single metric sample."""
        metric = await self.definition_repo.find_by_name(organization_id, metric_name)
        if not metric:
            raise ValueError(f"Metric '{metric_name}' not defined for organization")

        sample = MetricSample(
            metric_id=metric.id,
            organization_id=organization_id,
            value=value,
            labels=labels or {},
            timestamp=timestamp or now(),
        )

        # Save sample (in production, batch this)
        await self.sample_repo.save_batch([sample])

        # Check alert rules
        await self._check_alerts(metric, value, labels or {})

        return sample

    async def record_batch(
        self,
        organization_id: UUID,
        samples: list[dict[str, Any]],
    ) -> list[MetricSample]:
        """Record multiple metric samples at once."""
        metric_samples = []
        for s in samples:
            metric = await self.definition_repo.find_by_name(organization_id, s["metric_name"])
            if not metric:
                continue
            sample = MetricSample(
                metric_id=metric.id,
                organization_id=organization_id,
                value=s["value"],
                labels=s.get("labels", {}),
                timestamp=s.get("timestamp", now()),
            )
            metric_samples.append(sample)

        return await self.sample_repo.save_batch(metric_samples)

    async def query_metric(
        self,
        organization_id: UUID,
        metric_name: str,
        start: datetime,
        end: datetime,
        aggregation: str = "avg",
        labels: dict[str, str] | None = None,
    ) -> float:
        """Query aggregated metric value over time range."""
        metric = await self.definition_repo.find_by_name(organization_id, metric_name)
        if not metric:
            raise ValueError(f"Metric '{metric_name}' not found")

        return await self.sample_repo.aggregate(
            metric_id=metric.id,
            start=start,
            end=end,
            aggregation=aggregation,
            labels=labels,
        )

    async def get_metric_series(
        self,
        organization_id: UUID,
        metric_name: str,
        start: datetime,
        end: datetime,
        labels: dict[str, str] | None = None,
        interval_seconds: int = 60,
    ) -> list[dict[str, Any]]:
        """Get time series data for a metric."""
        metric = await self.definition_repo.find_by_name(organization_id, metric_name)
        if not metric:
            raise ValueError(f"Metric '{metric_name}' not found")

        samples = await self.sample_repo.find_by_metric(
            metric_id=metric.id,
            start=start,
            end=end,
            labels=labels,
        )

        # Group by interval
        if interval_seconds > 0:
            return self._bucket_samples(samples, interval_seconds)

        return [s.to_dict() for s in samples]

    def _bucket_samples(self, samples: list, interval_seconds: int) -> list[dict[str, Any]]:
        """Bucket samples into time intervals."""
        buckets: dict[int, list[float]] = {}
        for s in samples:
            bucket = int(s.timestamp.timestamp() / interval_seconds) * interval_seconds
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append(s.value)

        result = []
        for bucket_ts, values in sorted(buckets.items()):
            result.append({
                "timestamp": datetime.fromtimestamp(bucket_ts).isoformat(),
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "sum": sum(values),
            })
        return result


class AlertingService:
    """Service for managing and evaluating alert rules."""

    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        alert_repo: AlertRepository,
        metrics_service: MetricsService,
    ) -> None:
        self.rule_repo = rule_repo
        self.alert_repo = alert_repo
        self.metrics_service = metrics_service

    async def create_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule."""
        rule.created_at = now()
        rule.updated_at = now()
        return await self.rule_repo.save(rule)

    async def evaluate_rules(self) -> list[Alert]:
        """Evaluate all active alert rules and fire alerts as needed."""
        rules = await self.rule_repo.find_for_evaluation(now())
        fired_alerts = []

        for rule in rules:
            try:
                alerts = await self._evaluate_rule(rule)
                fired_alerts.extend(alerts)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.id}: {e}")

        return fired_alerts

    async def _evaluate_rule(self, rule: AlertRule) -> list[Alert]:
        """Evaluate a single alert rule."""
        # Query the metric
        end = now()
        start = end - timedelta(seconds=rule.evaluation_window_seconds)

        # In production, this would query the actual metric store
        # For now, return empty - actual implementation would query metric store
        return []

    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> Alert:
        alert = await self.alert_repo.find_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = now()
        alert.acknowledged_by = user_id
        alert.updated_at = now()
        return await self.alert_repo.save(alert)

    async def resolve_alert(self, alert_id: UUID, user_id: UUID) -> Alert:
        alert = await self.alert_repo.find_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = now()
        alert.resolved_by = user_id
        alert.updated_at = now()
        return await self.alert_repo.save(alert)


class CostTrackingService:
    """Service for tracking and analyzing costs."""

    def __init__(
        self,
        cost_repo: CostRecordRepository,
        budget_repo: BudgetRepository,
    ) -> None:
        self.cost_repo = cost_repo
        self.budget_repo = budget_repo

    async def record_cost(self, record: CostRecord) -> CostRecord:
        """Record a cost entry."""
        record.created_at = now()
        record.updated_at = now()
        saved = await self.cost_repo.save(record)

        # Check budget thresholds
        await self._check_budgets(record)

        return saved

    async def _check_budgets(self, record: CostRecord) -> None:
        budgets = await self.budget_repo.find_by_scope(
            record.organization_id,
            record.project_id,
            record.campaign_id,
        )

        for budget in budgets:
            if not budget.is_active:
                continue

            # Update current spend
            budget.current_spend_usd += record.amount_usd
            budget.updated_at = now()

            # Check thresholds
            if budget.is_over_critical():
                # Fire critical budget alert
                pass
            elif budget.is_over_warning():
                # Fire warning budget alert
                pass

            await self.budget_repo.save(budget)

    async def get_cost_report(
        self,
        organization_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """Generate a cost report for a period."""
        records = await self.cost_repo.find_by_organization(
            organization_id, period_start, period_end
        )

        total = sum(r.amount_usd for r in records)
        by_category: dict[str, float] = {}
        by_resource: dict[str, float] = {}
        by_project: dict[str, float] = {}
        by_campaign: dict[str, float] = {}
        by_provider: dict[str, float] = {}

        for r in records:
            by_category[r.category.value] = by_category.get(r.category.value, 0) + r.amount_usd
            by_resource[r.resource_type] = by_resource.get(r.resource_type, 0) + r.amount_usd
            if r.project_id:
                by_project[str(r.project_id)] = by_project.get(str(r.project_id), 0) + r.amount_usd
            if r.campaign_id:
                by_campaign[str(r.campaign_id)] = by_campaign.get(str(r.campaign_id), 0) + r.amount_usd
            if r.provider:
                by_provider[r.provider] = by_provider.get(r.provider, 0) + r.amount_usd

        # Daily trend
        daily = self._aggregate_daily(records)

        # Budget info
        budgets = await self.budget_repo.find_by_organization(organization_id, active_only=True)
        total_budget = sum(b.amount_usd for b in budgets)
        budget_util = sum(b.current_spend_usd for b in budgets) / total_budget if total_budget > 0 else 0

        return {
            "total_cost_usd": total,
            "cost_by_category": by_category,
            "cost_by_resource": by_resource,
            "cost_by_project": by_project,
            "cost_by_campaign": by_campaign,
            "cost_by_provider": by_provider,
            "daily_costs": daily,
            "total_budget_usd": total_budget,
            "budget_utilization_pct": budget_util * 100,
        }

    def _aggregate_daily(self, records: list[CostRecord]) -> list[dict[str, Any]]:
        daily: dict[str, float] = {}
        for r in records:
            day = r.period_start.date().isoformat()
            daily[day] = daily.get(day, 0) + r.amount_usd
        return [{"date": d, "cost_usd": c} for d, c in sorted(daily.items())]


class SLAService:
    """Service for SLA monitoring and reporting."""

    def __init__(
        self,
        sla_repo: SLARepository,
        report_repo: SLAReportRepository,
    ) -> None:
        self.sla_repo = sla_repo
        self.report_repo = report_repo

    async def create_sla(self, sla: SLADefinition) -> SLADefinition:
        sla.created_at = now()
        sla.updated_at = now()
        return await self.sla_repo.save(sla)

    async def generate_report(
        self,
        sla_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> SLAReport:
        """Generate an SLA compliance report for a period."""
        sla = await self.sla_repo.find_by_id(sla_id)
        if not sla:
            raise ValueError(f"SLA {sla_id} not found")

        # In production, this would query actual metrics
        # For now, return a mock report
        report = SLAReport(
            organization_id=uuid4(),  # Would come from SLA
            sla_definition_id=sla_id,
            period_start=period_start,
            period_end=period_end,
            measured_value=99.95,
            target_value=sla.target_value,
            unit=sla.target_unit,
            is_compliant=True,
            breach_count=0,
            total_downtime_seconds=0.0,
            incidents=[],
            generated_by=uuid4(),
        )

        return await self.report_repo.save(report)

    async def get_sla_status(self, sla_id: UUID) -> dict[str, Any]:
        """Get current SLA status."""
        sla = await self.sla_repo.find_by_id(sla_id)
        if not sla:
            raise ValueError(f"SLA {sla_id} not found")

        # In production, query actual metrics
        return {
            "sla": sla.to_dict(),
            "current_value": 99.95,
            "target_value": sla.target_value,
            "is_compliant": True,
            "time_to_breach": None,
        }


class DashboardService:
    """Service for managing dashboards and widgets."""

    def __init__(
        self,
        dashboard_repo: DashboardRepository,
        widget_repo: DashboardWidgetRepository,
    ) -> None:
        self.dashboard_repo = dashboard_repo
        self.widget_repo = widget_repo

    async def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        dashboard.created_at = now()
        dashboard.updated_at = now()
        return await self.dashboard_repo.save(dashboard)

    async def get_dashboard(self, dashboard_id: UUID) -> Dashboard | None:
        dashboard = await self.dashboard_repo.find_by_id(dashboard_id)
        if dashboard:
            dashboard.widgets = await self.widget_repo.find_by_dashboard(dashboard.id)
        return dashboard

    async def list_dashboards(self, organization_id: UUID) -> list[Dashboard]:
        return await self.dashboard_repo.find_by_organization(organization_id)

    async def get_default_dashboard(self, organization_id: UUID) -> Dashboard | None:
        return await self.dashboard_repo.find_default(organization_id)

    async def create_widget(self, widget: DashboardWidget) -> DashboardWidget:
        widget.created_at = now()
        widget.updated_at = now()
        return await self.widget_repo.save(widget)

    async def update_widget(self, widget: DashboardWidget) -> DashboardWidget:
        widget.updated_at = now()
        return await self.widget_repo.save(widget)

    async def delete_widget(self, widget_id: UUID) -> None:
        # In production, implement delete
        pass


class SystemHealthService:
    """Service for generating system health reports."""

    def __init__(
        self,
        metrics_service: MetricsService,
        alerting_service: AlertingService,
        cost_service: CostTrackingService,
        sla_service: SLAService,
    ) -> None:
        self.metrics_service = metrics_service
        self.alerting_service = alerting_service
        self.cost_service = cost_service
        self.sla_service = sla_service

    async def generate_health_report(self, organization_id: UUID) -> dict[str, Any]:
        """Generate a comprehensive system health report."""
        # Get active alerts
        # In production, inject these properly

        # For now, return mock data structure
        return {
            "organization_id": str(organization_id),
            "timestamp": now().isoformat(),
            "overall_status": "healthy",
            "components": {
                "api": {"status": "healthy", "latency_p99_ms": 45, "error_rate_pct": 0.01},
                "database": {"status": "healthy", "connections_used_pct": 45, "latency_p99_ms": 12},
                "cache": {"status": "healthy", "hit_rate_pct": 98.5, "memory_used_pct": 60},
                "queue": {"status": "healthy", "depth": 15, "processing_rate_per_sec": 120},
            },
            "key_metrics": {
                "requests_per_second": 1250,
                "avg_latency_ms": 52,
                "error_rate_pct": 0.01,
                "active_users": 2340,
            },
            "active_alerts": 2,
            "critical_alerts": 0,
            "sla_compliance": {
                "api_availability": 99.97,
                "api_latency_p99": 99.8,
            },
            "current_month_cost_usd": 12500.50,
            "budget_utilization_pct": 72.5,
        }


# --- Helper Functions ---

def generate_fingerprint(rule_id: UUID, labels: dict[str, str]) -> str:
    """Generate a fingerprint for alert deduplication."""
    import hashlib
    key = f"{rule_id}:{sorted(labels.items())}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def parse_alert_condition(condition: str) -> tuple[str, str, float]:
    """Parse alert condition string like 'avg > 100'."""
    import re
    match = re.match(r"(\w+)\s*(>=|<=|>|<|==|!=)\s*([\d.]+)", condition)
    if not match:
        raise ValueError(f"Invalid condition: {condition}")
    return match.groups()


# --- Singleton Instances ---

metrics_service = None
alerting_service = None
cost_tracking_service = None
sla_service = None
dashboard_service = None
system_health_service = None
