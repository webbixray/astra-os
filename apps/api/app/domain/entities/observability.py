"""Observability Entities — E6.4 Beta Launch.

Entities for advanced monitoring, alerting, cost tracking, and SLA reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now

# --- Enums ---


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertSource(str, Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS = "business"
    SECURITY = "security"


class MetricType(str, Enum):
    GAUGE = "gauge"  # Point-in-time value
    COUNTER = "counter"  # Monotonically increasing
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Quantile summaries


class CostCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    AI_INFERENCE = "ai_inference"
    API_CALLS = "api_calls"
    EXTERNAL_API = "external_api"
    PERSONNEL = "personnel"
    OTHER = "other"


class SLAType(str, Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    DATA_FRESHNESS = "data_freshness"


class DashboardWidgetType(str, Enum):
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    GAUGE = "gauge"
    STAT_VALUE = "stat_value"
    TABLE = "table"
    HEATMAP = "heatmap"
    PIE_CHART = "pie_chart"


# --- Entities ---


@dataclass
class MetricDefinition:
    """Definition of a metric that can be collected and queried."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    display_name: str = ""
    description: str = ""
    metric_type: MetricType = MetricType.GAUGE
    unit: str = ""  # e.g., "ms", "bytes", "count", "USD"

    # Labels/dimensions
    label_names: list[str] = field(default_factory=list)  # e.g., ["endpoint", "method", "status"]

    # Collection
    collection_interval_seconds: int = 60
    retention_days: int = 30

    # Alerting
    alert_thresholds: dict[str, Any] = field(
        default_factory=dict
    )  # e.g., {"warning": 100, "critical": 500}

    # Metadata
    tags: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "metric_type": self.metric_type.value,
            "unit": self.unit,
            "label_names": self.label_names,
            "collection_interval_seconds": self.collection_interval_seconds,
            "retention_days": self.retention_days,
            "alert_thresholds": self.alert_thresholds,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class MetricSample:
    """A single sample of a metric at a point in time."""

    id: UUID = field(default_factory=uuid4)
    metric_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now)

    # For histogram/summary
    bucket_counts: dict[str, int] = field(default_factory=dict)
    quantiles: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "metric_id": str(self.metric_id),
            "organization_id": str(self.organization_id),
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "bucket_counts": self.bucket_counts,
            "quantiles": self.quantiles,
        }


@dataclass
class AlertRule:
    """Definition of an alerting rule."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    source: AlertSource = AlertSource.APPLICATION
    severity: AlertSeverity = AlertSeverity.WARNING

    # Condition
    metric_name: str = ""
    condition: str = ""  # e.g., "avg > 100", "count > 10"
    evaluation_window_seconds: int = 300  # 5 minutes

    # Labels to match
    label_matchers: dict[str, str] = field(default_factory=dict)

    # Notification
    notification_channels: list[str] = field(
        default_factory=list
    )  # email, slack, pagerduty, webhook
    notification_template: str = ""

    # Behavior
    auto_resolve: bool = True
    resolve_timeout_seconds: int = 3600
    group_by: list[str] = field(default_factory=list)  # Group alerts by these labels

    # Scheduling
    active_hours: dict[str, Any] | None = (
        None  # e.g., {"start": "09:00", "end": "17:00", "days": [1,2,3,4,5]}
    )

    # Metadata
    tags: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "severity": self.severity.value,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "evaluation_window_seconds": self.evaluation_window_seconds,
            "label_matchers": self.label_matchers,
            "notification_channels": self.notification_channels,
            "auto_resolve": self.auto_resolve,
            "resolve_timeout_seconds": self.resolve_timeout_seconds,
            "group_by": self.group_by,
            "active_hours": self.active_hours,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Alert:
    """An active or historical alert instance."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    alert_rule_id: UUID = field(default_factory=uuid4)

    # Alert details
    status: AlertStatus = AlertStatus.FIRING
    severity: AlertSeverity = AlertSeverity.WARNING
    title: str = ""
    description: str = ""

    # Context
    metric_name: str = ""
    metric_value: float = 0.0
    threshold_value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    # Timeline
    started_at: datetime = field(default_factory=now)
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None

    # Deduplication
    fingerprint: str = ""  # For deduplication
    count: int = 1  # Number of times this alert has fired

    # Metadata
    annotations: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "alert_rule_id": str(self.alert_rule_id),
            "status": self.status.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "labels": self.labels,
            "started_at": self.started_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": str(self.acknowledged_by) if self.acknowledged_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "fingerprint": self.fingerprint,
            "count": self.count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def is_active(self) -> bool:
        return self.status in (AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED)

    def duration_seconds(self) -> float:
        end = self.resolved_at or now()
        return (end - self.started_at).total_seconds()


@dataclass
class CostRecord:
    """A cost entry for tracking expenses."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Cost details
    category: CostCategory = CostCategory.OTHER
    amount_usd: float = 0.0
    currency: str = "USD"

    # Attribution
    resource_type: str = ""  # e.g., "compute", "api", "storage"
    resource_id: str = ""  # Specific resource identifier
    project_id: UUID | None = None
    campaign_id: UUID | None = None

    # Details
    quantity: float = 0.0
    unit: str = ""  # e.g., "hours", "gb", "million_tokens", "requests"
    unit_cost_usd: float = 0.0

    # Time
    period_start: datetime = field(default_factory=now)
    period_end: datetime = field(default_factory=now)

    # Metadata
    provider: str = ""  # e.g., "aws", "gcp", "openai", "anthropic"
    invoice_id: str = ""
    tags: list[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "category": self.category.value,
            "amount_usd": self.amount_usd,
            "currency": self.currency,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": str(self.project_id) if self.project_id else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_cost_usd": self.unit_cost_usd,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "provider": self.provider,
            "invoice_id": self.invoice_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Budget:
    """Budget definition for cost control."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""

    # Budget amount
    amount_usd: float = 0.0
    currency: str = "USD"
    period: str = "monthly"  # daily, weekly, monthly, quarterly, yearly

    # Scope
    category: CostCategory | None = None  # None = all categories
    project_id: UUID | None = None
    campaign_id: UUID | None = None

    # Thresholds
    warning_threshold_pct: float = 0.8  # Alert at 80%
    critical_threshold_pct: float = 0.95  # Alert at 95%
    hard_limit: bool = False  # If true, block spending at limit

    # Behavior
    auto_renew: bool = True
    rollover_unused: bool = False

    # Current state
    current_spend_usd: float = 0.0
    period_start: datetime = field(default_factory=now)
    period_end: datetime = field(default_factory=now)

    # Metadata
    is_active: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "amount_usd": self.amount_usd,
            "currency": self.currency,
            "period": self.period,
            "category": self.category.value if self.category else None,
            "warning_threshold_pct": self.warning_threshold_pct,
            "critical_threshold_pct": self.critical_threshold_pct,
            "hard_limit": self.hard_limit,
            "current_spend_usd": self.current_spend_usd,
            "spend_pct": self.current_spend_usd / self.amount_usd if self.amount_usd > 0 else 0,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def is_over_warning(self) -> bool:
        if self.amount_usd == 0:
            return False
        return (self.current_spend_usd / self.amount_usd) >= self.warning_threshold_pct

    def is_over_critical(self) -> bool:
        if self.amount_usd == 0:
            return False
        return (self.current_spend_usd / self.amount_usd) >= self.critical_threshold_pct

    def is_exhausted(self) -> bool:
        return self.current_spend_usd >= self.amount_usd


@dataclass
class SLADefinition:
    """Service Level Agreement definition."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""

    # SLA type and target
    sla_type: SLAType = SLAType.AVAILABILITY
    target_value: float = 99.9  # e.g., 99.9% availability
    target_unit: str = "%"  # %, ms, req/s, etc.

    # Scope
    service_name: str = ""
    endpoint_pattern: str = ""  # Regex pattern for endpoints

    # Measurement window
    measurement_window: str = "monthly"  # daily, weekly, monthly, quarterly

    # Thresholds
    warning_threshold: float = 99.95  # Alert when approaching breach
    critical_threshold: float = 99.9  # SLA breach threshold

    # Business hours
    business_hours_only: bool = False
    business_hours: dict[str, Any] | None = None

    # Penalty/credit
    penalty_per_breach: float = 0.0
    credit_percentage: float = 0.0

    # Metadata
    is_active: bool = True
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "sla_type": self.sla_type.value,
            "target_value": self.target_value,
            "target_unit": self.target_unit,
            "service_name": self.service_name,
            "endpoint_pattern": self.endpoint_pattern,
            "measurement_window": self.measurement_window,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "business_hours_only": self.business_hours_only,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SLAReport:
    """SLA compliance report for a period."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    sla_definition_id: UUID = field(default_factory=uuid4)

    # Period
    period_start: datetime = field(default_factory=now)
    period_end: datetime = field(default_factory=now)

    # Measurements
    measured_value: float = 0.0
    target_value: float = 0.0
    unit: str = ""

    # Compliance
    is_compliant: bool = True
    breach_count: int = 0
    total_downtime_seconds: float = 0.0

    # Incidents
    incidents: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=now)
    generated_by: UUID | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "sla_definition_id": str(self.sla_definition_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "measured_value": self.measured_value,
            "target_value": self.target_value,
            "unit": self.unit,
            "is_compliant": self.is_compliant,
            "breach_count": self.breach_count,
            "total_downtime_seconds": self.total_downtime_seconds,
            "incidents": self.incidents,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class Dashboard:
    """Customizable dashboard for a team/organization."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""

    # Layout
    layout: dict[str, Any] = field(default_factory=dict)  # Grid layout config

    # Sharing
    is_public: bool = False
    shared_with: list[UUID] = field(default_factory=list)  # User IDs

    # Refresh
    auto_refresh_seconds: int = 300

    # Metadata
    tags: list[str] = field(default_factory=list)
    is_default: bool = False
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "layout": self.layout,
            "is_public": self.is_public,
            "shared_with": [str(u) for u in self.shared_with],
            "auto_refresh_seconds": self.auto_refresh_seconds,
            "tags": self.tags,
            "is_default": self.is_default,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DashboardWidget:
    """A widget on a dashboard."""

    id: UUID = field(default_factory=uuid4)
    dashboard_id: UUID = field(default_factory=uuid4)

    # Widget config
    widget_type: DashboardWidgetType = DashboardWidgetType.LINE_CHART
    title: str = ""
    description: str = ""

    # Data source
    metric_names: list[str] = field(default_factory=list)
    query: str = ""  # Query string for data

    # Visualization
    visualization_config: dict[str, Any] = field(default_factory=dict)  # Colors, axes, etc.

    # Layout
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4

    # Time range
    time_range_seconds: int = 3600  # Last hour by default
    refresh_interval_seconds: int = 60

    # Filters
    filters: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "dashboard_id": str(self.dashboard_id),
            "widget_type": self.widget_type.value,
            "title": self.title,
            "description": self.description,
            "metric_names": self.metric_names,
            "query": self.query,
            "visualization_config": self.visualization_config,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "width": self.width,
            "height": self.height,
            "time_range_seconds": self.time_range_seconds,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "filters": self.filters,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# --- Analytics ---


@dataclass
class SystemHealthReport:
    """Overall system health snapshot."""

    organization_id: UUID
    timestamp: datetime = field(default_factory=now)

    # Overall status
    overall_status: str = "healthy"  # healthy, degraded, critical

    # Components
    components: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Key metrics
    key_metrics: dict[str, Any] = field(default_factory=dict)

    # Active alerts
    active_alerts: int = 0
    critical_alerts: int = 0

    # SLA compliance
    sla_compliance: dict[str, float] = field(default_factory=dict)

    # Cost
    current_month_cost_usd: float = 0.0
    budget_utilization_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id),
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status,
            "components": self.components,
            "key_metrics": self.key_metrics,
            "active_alerts": self.active_alerts,
            "critical_alerts": self.critical_alerts,
            "sla_compliance": self.sla_compliance,
            "current_month_cost_usd": self.current_month_cost_usd,
            "budget_utilization_pct": self.budget_utilization_pct,
        }


@dataclass
class CostReport:
    """Cost analysis report for a period."""

    organization_id: UUID
    period_start: datetime
    period_end: datetime

    # Totals
    total_cost_usd: float = 0.0
    cost_by_category: dict[str, float] = field(default_factory=dict)
    cost_by_resource: dict[str, float] = field(default_factory=dict)
    cost_by_project: dict[str, float] = field(default_factory=dict)
    cost_by_campaign: dict[str, float] = field(default_factory=dict)
    cost_by_provider: dict[str, float] = field(default_factory=dict)

    # Trends
    daily_costs: list[dict[str, Any]] = field(default_factory=list)
    cost_trend_pct: float = 0.0  # % change vs previous period

    # Budget
    total_budget_usd: float = 0.0
    budget_utilization_pct: float = 0.0
    budgets_over_warning: int = 0
    budgets_over_critical: int = 0

    # Projections
    projected_month_end_cost_usd: float = 0.0
    projected_vs_budget_pct: float = 0.0

    # Savings opportunities
    savings_opportunities: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_cost_usd": self.total_cost_usd,
            "cost_by_category": self.cost_by_category,
            "cost_by_resource": self.cost_by_resource,
            "cost_by_project": self.cost_by_project,
            "cost_by_campaign": self.cost_by_campaign,
            "cost_by_provider": self.cost_by_provider,
            "daily_costs": self.daily_costs,
            "cost_trend_pct": self.cost_trend_pct,
            "total_budget_usd": self.total_budget_usd,
            "budget_utilization_pct": self.budget_utilization_pct,
            "budgets_over_warning": self.budgets_over_warning,
            "budgets_over_critical": self.budgets_over_critical,
            "projected_month_end_cost_usd": self.projected_month_end_cost_usd,
            "projected_vs_budget_pct": self.projected_vs_budget_pct,
            "savings_opportunities": self.savings_opportunities,
        }
