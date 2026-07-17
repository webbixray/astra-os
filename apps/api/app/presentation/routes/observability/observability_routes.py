"""Observability API Routes — E6.4 Beta Launch.

Endpoints for metrics, alerting, cost tracking, SLA monitoring, dashboards, and system health.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.observability import (
    AlertRule,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    Budget,
    BudgetCategory,
    CostRecord,
    Dashboard,
    DashboardWidget,
    DashboardWidgetType,
    MetricDefinition,
    MetricType,
    SLADefinition,
    SLAType,
)
from app.domain.services.observability import (
    AlertingService,
    CostTrackingService,
    DashboardService,
    MetricsService,
    SLAService,
    SystemHealthService,
)
from app.presentation.dependencies import get_db
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role

router = APIRouter(prefix="/observability", tags=["observability"])


# --- Request/Response Models ---

class MetricDefinitionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    display_name: str = ""
    description: str = ""
    metric_type: MetricType = MetricType.GAUGE
    unit: str = ""
    label_names: list[str] = Field(default_factory=list)
    collection_interval_seconds: int = Field(default=60, ge=10, le=3600)
    retention_days: int = Field(default=30, ge=1, le=365)
    alert_thresholds: dict[str, float] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class MetricSampleRequest(BaseModel):
    metric_name: str
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime | None = None


class AlertRuleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    source: str = "application"
    severity: AlertSeverity = AlertSeverity.WARNING
    metric_name: str = ""
    condition: str = ""
    evaluation_window_seconds: int = Field(default=300, ge=60, le=86400)
    label_matchers: dict[str, str] = Field(default_factory=dict)
    notification_channels: list[str] = Field(default_factory=list)
    auto_resolve: bool = True
    resolve_timeout_seconds: int = Field(default=3600, ge=60)
    group_by: list[str] = Field(default_factory=list)
    active_hours: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)


class CostRecordRequest(BaseModel):
    category: BudgetCategory
    amount_usd: float = Field(ge=0)
    currency: str = "USD"
    resource_type: str = ""
    resource_id: str = ""
    project_id: str | None = None
    campaign_id: str | None = None
    quantity: float = Field(default=0, ge=0)
    unit: str = ""
    unit_cost_usd: float = Field(default=0, ge=0)
    provider: str = ""
    invoice_id: str = ""
    tags: list[str] = Field(default_factory=list)


class BudgetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    amount_usd: float = Field(ge=0)
    currency: str = "USD"
    period: str = Field(pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    category: BudgetCategory | None = None
    project_id: str | None = None
    campaign_id: str | None = None
    warning_threshold_pct: float = Field(default=0.8, ge=0, le=1)
    critical_threshold_pct: float = Field(default=0.95, ge=0, le=1)
    hard_limit: bool = False
    auto_renew: bool = True
    rollover_unused: bool = False


class SLADefinitionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    sla_type: SLAType
    target_value: float = Field(gt=0)
    target_unit: str = ""
    service_name: str = ""
    endpoint_pattern: str = ""
    measurement_window: str = Field(pattern="^(daily|weekly|monthly|quarterly)$")
    warning_threshold: float = Field(ge=0, le=100)
    critical_threshold: float = Field(ge=0, le=100)
    business_hours_only: bool = False
    business_hours: dict[str, Any] | None = None
    penalty_per_breach: float = Field(default=0, ge=0)
    credit_percentage: float = Field(default=0, ge=0, le=100)


class SLAReportRequest(BaseModel):
    sla_id: str
    period_start: datetime
    period_end: datetime


class DashboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    layout: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    shared_with: list[str] = Field(default_factory=list)
    auto_refresh_seconds: int = Field(default=300, ge=30)
    tags: list[str] = Field(default_factory=list)
    is_default: bool = False


class DashboardWidgetRequest(BaseModel):
    dashboard_id: str
    widget_type: DashboardWidgetType
    title: str = ""
    description: str = ""
    metric_names: list[str] = Field(default_factory=list)
    query: str = ""
    visualization_config: dict[str, Any] = Field(default_factory=dict)
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    width: int = Field(default=6, ge=1, le=12)
    height: int = Field(default=4, ge=1, le=12)
    time_range_seconds: int = Field(default=3600, ge=60)
    refresh_interval_seconds: int = Field(default=60, ge=10)
    filters: dict[str, Any] = Field(default_factory=dict)


class RecordMetricRequest(BaseModel):
    metric_name: str
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime | None = None


class AlertAcknowledgeRequest(BaseModel):
    alert_id: str
    user_id: str


# --- Dependencies ---

async def _require_org_access(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "viewer", user_id, db)
    return organization_id


async def _require_org_admin(
    organization_id: UUID,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    await require_org_role(organization_id, "admin", user_id, db)
    return organization_id


def get_metrics_service(db: AsyncSession = Depends(get_db)) -> MetricsService:
    from app.infrastructure.db.repositories.alerting_repository import AlertRuleRepositoryImpl
    from app.infrastructure.db.repositories.metrics_repository import (
        MetricDefinitionRepositoryImpl,
        MetricSampleRepositoryImpl,
    )
    definition_repo = MetricDefinitionRepositoryImpl(db)
    sample_repo = MetricSampleRepositoryImpl(db)
    alert_repo = AlertRuleRepositoryImpl(db)
    return MetricsService(definition_repo, sample_repo, alert_repo)


def get_alerting_service(db: AsyncSession = Depends(get_db)) -> AlertingService:
    from app.infrastructure.db.repositories.alerting_repository import AlertRepositoryImpl, AlertRuleRepositoryImpl
    rule_repo = AlertRuleRepositoryImpl(db)
    alert_repo = AlertRepositoryImpl(db)
    metrics_service = get_metrics_service(db)
    return AlertingService(rule_repo, alert_repo, metrics_service)


def get_cost_service(db: AsyncSession = Depends(get_db)) -> CostTrackingService:
    from app.infrastructure.db.repositories.cost_repository import (
        BudgetRepositoryImpl,
        CostRecordRepositoryImpl,
    )
    cost_repo = CostRecordRepositoryImpl(db)
    budget_repo = BudgetRepositoryImpl(db)
    return CostTrackingService(cost_repo, budget_repo)


def get_sla_service(db: AsyncSession = Depends(get_db)) -> SLAService:
    from app.infrastructure.db.repositories.sla_repository import (
        SLAReportRepositoryImpl,
        SLARepositoryImpl,
    )
    sla_repo = SLARepositoryImpl(db)
    report_repo = SLAReportRepositoryImpl(db)
    return SLAService(sla_repo, report_repo)


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    from app.infrastructure.db.repositories.dashboard_repository import (
        DashboardRepositoryImpl,
        DashboardWidgetRepositoryImpl,
    )
    dashboard_repo = DashboardRepositoryImpl(db)
    widget_repo = DashboardWidgetRepositoryImpl(db)
    return DashboardService(dashboard_repo, widget_repo)


def get_system_health_service(
    db: AsyncSession = Depends(get_db),
) -> SystemHealthService:
    metrics_service = get_metrics_service(db)
    alerting_service = get_alerting_service(db)
    cost_service = get_cost_service(db)
    sla_service = get_sla_service(db)
    return SystemHealthService(
        metrics_service, alerting_service, cost_service, sla_service
    )


# --- Metrics Routes ---

@router.post(
    "/organizations/{organization_id}/metrics/definitions",
    status_code=status.HTTP_201_CREATED,
    summary="Create a metric definition",
)
async def create_metric_definition(
    organization_id: UUID,
    request: MetricDefinitionRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    metric = MetricDefinition(
        organization_id=organization_id,
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        metric_type=request.metric_type,
        unit=request.unit,
        label_names=request.label_names,
        collection_interval_seconds=request.collection_interval_seconds,
        retention_days=request.retention_days,
        alert_thresholds=request.alert_thresholds,
        tags=request.tags,
    )
    # In production, save via repository
    return metric.to_dict()


@router.get(
    "/organizations/{organization_id}/metrics/definitions",
    summary="List metric definitions",
)
async def list_metric_definitions(
    organization_id: UUID,
    active_only: bool = Query(True),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> list[dict]:
    # In production, query repository
    return []


@router.post(
    "/organizations/{organization_id}/metrics/record",
    status_code=status.HTTP_201_CREATED,
    summary="Record a metric sample",
)
async def record_metric(
    organization_id: UUID,
    request: RecordMetricRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    sample = await service.record_metric(
        organization_id=organization_id,
        metric_name=request.metric_name,
        value=request.value,
        labels=request.labels,
        timestamp=request.timestamp,
    )
    return sample.to_dict()


@router.post(
    "/organizations/{organization_id}/metrics/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Record multiple metric samples",
)
async def record_metrics_batch(
    organization_id: UUID,
    samples: list[MetricSampleRequest],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> list[dict]:
    samples_data = [s.model_dump() for s in samples]
    recorded = await service.record_batch(organization_id, samples_data)
    return [s.to_dict() for s in recorded]


@router.get(
    "/organizations/{organization_id}/metrics/{metric_name}/query",
    summary="Query metric aggregation",
)
async def query_metric(
    organization_id: UUID,
    metric_name: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    aggregation: str = Query("avg", pattern="^(sum|avg|min|max|count|p50|p90|p95|p99)$"),
    labels: dict[str, str] | None = Query(None),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    value = await service.query_metric(
        organization_id=organization_id,
        metric_name=metric_name,
        start=start,
        end=end,
        aggregation=aggregation,
        labels=labels,
    )
    return {"metric": metric_name, "aggregation": aggregation, "value": value, "start": start.isoformat(), "end": end.isoformat()}


@router.get(
    "/organizations/{organization_id}/metrics/{metric_name}/series",
    summary="Get metric time series",
)
async def get_metric_series(
    organization_id: UUID,
    metric_name: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    labels: dict[str, str] | None = Query(None),
    interval_seconds: int = Query(60, ge=10, le=3600),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> list[dict]:
    return await service.get_metric_series(
        organization_id=organization_id,
        metric_name=metric_name,
        start=start,
        end=end,
        labels=labels,
        interval_seconds=interval_seconds,
    )


# --- Alerting Routes ---

@router.post(
    "/organizations/{organization_id}/alerts/rules",
    status_code=status.HTTP_201_CREATED,
    summary="Create an alert rule",
)
async def create_alert_rule(
    organization_id: UUID,
    request: AlertRuleRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: AlertingService = Depends(get_alerting_service),
) -> dict:
    rule = AlertRule(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        source=AlertSource(request.source),
        severity=AlertSeverity(request.severity),
        metric_name=request.metric_name,
        condition=request.condition,
        evaluation_window_seconds=request.evaluation_window_seconds,
        label_matchers=request.label_matchers,
        notification_channels=request.notification_channels,
        auto_resolve=request.auto_resolve,
        resolve_timeout_seconds=request.resolve_timeout_seconds,
        group_by=request.group_by,
        active_hours=request.active_hours,
        tags=request.tags,
    )
    created = await service.create_rule(rule)
    return created.to_dict()


@router.get(
    "/organizations/{organization_id}/alerts/rules",
    summary="List alert rules",
)
async def list_alert_rules(
    organization_id: UUID,
    active_only: bool = Query(True),
    org_id: UUID = Depends(_require_org_access),
    service: AlertingService = Depends(get_alerting_service),
) -> list[dict]:
    return []


@router.post(
    "/organizations/{organization_id}/alerts/evaluate",
    summary="Evaluate all alert rules",
)
async def evaluate_alerts(
    organization_id: UUID,
    org_id: UUID = Depends(_require_org_admin),
    service: AlertingService = Depends(get_alerting_service),
) -> dict:
    alerts = await service.evaluate_rules()
    return {"evaluated": len(alerts), "alerts": [a.to_dict() for a in alerts]}


@router.get(
    "/organizations/{organization_id}/alerts",
    summary="List alerts",
)
async def list_alerts(
    organization_id: UUID,
    status: AlertStatus | None = Query(None),
    severity: AlertSeverity | None = Query(None),
    limit: int = Query(100, le=500),
    org_id: UUID = Depends(_require_org_access),
    service: AlertingService = Depends(get_alerting_service),
) -> list[dict]:
    return []


@router.post(
    "/organizations/{organization_id}/alerts/acknowledge",
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    organization_id: UUID,
    request: AlertAcknowledgeRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: AlertingService = Depends(get_alerting_service),
) -> dict:
    alert = await service.acknowledge_alert(UUID(request.alert_id), user_id)
    return alert.to_dict()


@router.post(
    "/organizations/{organization_id}/alerts/resolve",
    summary="Resolve an alert",
)
async def resolve_alert(
    organization_id: UUID,
    request: AlertAcknowledgeRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: AlertingService = Depends(get_alerting_service),
) -> dict:
    alert = await service.resolve_alert(UUID(request.alert_id), user_id)
    return alert.to_dict()


# --- Cost Tracking Routes ---

@router.post(
    "/organizations/{organization_id}/costs",
    status_code=status.HTTP_201_CREATED,
    summary="Record a cost entry",
)
async def record_cost(
    organization_id: UUID,
    request: CostRecordRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: CostTrackingService = Depends(get_cost_service),
) -> dict:
    record = CostRecord(
        organization_id=organization_id,
        category=request.category,
        amount_usd=request.amount_usd,
        currency=request.currency,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        project_id=UUID(request.project_id) if request.project_id else None,
        campaign_id=UUID(request.campaign_id) if request.campaign_id else None,
        quantity=request.quantity,
        unit=request.unit,
        unit_cost_usd=request.unit_cost_usd,
        provider=request.provider,
        invoice_id=request.invoice_id,
        tags=request.tags,
    )
    saved = await service.record_cost(record)
    return saved.to_dict()


@router.get(
    "/organizations/{organization_id}/costs/report",
    summary="Get cost report for a period",
)
async def get_cost_report(
    organization_id: UUID,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    org_id: UUID = Depends(_require_org_access),
    service: CostTrackingService = Depends(get_cost_service),
) -> dict:
    return await service.get_cost_report(organization_id, period_start, period_end)


@router.post(
    "/organizations/{organization_id}/budgets",
    status_code=status.HTTP_201_CREATED,
    summary="Create a budget",
)
async def create_budget(
    organization_id: UUID,
    request: BudgetRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: CostTrackingService = Depends(get_cost_service),
) -> dict:
    budget = Budget(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        amount_usd=request.amount_usd,
        currency=request.currency,
        period=request.period,
        category=request.category,
        project_id=UUID(request.project_id) if request.project_id else None,
        campaign_id=UUID(request.campaign_id) if request.campaign_id else None,
        warning_threshold_pct=request.warning_threshold_pct,
        critical_threshold_pct=request.critical_threshold_pct,
        hard_limit=request.hard_limit,
        auto_renew=request.auto_renew,
        rollover_unused=request.rollover_unused,
    )
    saved = await service.budget_repo.save(budget)
    return saved.to_dict()


@router.get(
    "/organizations/{organization_id}/budgets",
    summary="List budgets",
)
async def list_budgets(
    organization_id: UUID,
    active_only: bool = Query(True),
    org_id: UUID = Depends(_require_org_access),
    service: CostTrackingService = Depends(get_cost_service),
) -> list[dict]:
    budgets = await service.budget_repo.find_by_organization(organization_id, active_only=active_only)
    return [b.to_dict() for b in budgets]


# --- SLA Routes ---

@router.post(
    "/organizations/{organization_id}/slas",
    status_code=status.HTTP_201_CREATED,
    summary="Create an SLA definition",
)
async def create_sla(
    organization_id: UUID,
    request: SLADefinitionRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: SLAService = Depends(get_sla_service),
) -> dict:
    sla = SLADefinition(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        sla_type=request.sla_type,
        target_value=request.target_value,
        target_unit=request.target_unit,
        service_name=request.service_name,
        endpoint_pattern=request.endpoint_pattern,
        measurement_window=request.measurement_window,
        warning_threshold=request.warning_threshold,
        critical_threshold=request.critical_threshold,
        business_hours_only=request.business_hours_only,
        business_hours=request.business_hours,
        penalty_per_breach=request.penalty_per_breach,
        credit_percentage=request.credit_percentage,
    )
    created = await service.create_sla(sla)
    return created.to_dict()


@router.get(
    "/organizations/{organization_id}/slas",
    summary="List SLA definitions",
)
async def list_slas(
    organization_id: UUID,
    active_only: bool = Query(True),
    org_id: UUID = Depends(_require_org_access),
    service: SLAService = Depends(get_sla_service),
) -> list[dict]:
    return []


@router.post(
    "/organizations/{organization_id}/slas/report",
    status_code=status.HTTP_201_CREATED,
    summary="Generate SLA compliance report",
)
async def generate_sla_report(
    organization_id: UUID,
    request: SLAReportRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: SLAService = Depends(get_sla_service),
) -> dict:
    report = await service.generate_report(
        sla_id=UUID(request.sla_id),
        period_start=request.period_start,
        period_end=request.period_end,
    )
    return report.to_dict()


@router.get(
    "/organizations/{organization_id}/slas/{sla_id}/status",
    summary="Get SLA current status",
)
async def get_sla_status(
    organization_id: UUID,
    sla_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    service: SLAService = Depends(get_sla_service),
) -> dict:
    return await service.get_sla_status(sla_id)


# --- Dashboard Routes ---

@router.post(
    "/organizations/{organization_id}/dashboards",
    status_code=status.HTTP_201_CREATED,
    summary="Create a dashboard",
)
async def create_dashboard(
    organization_id: UUID,
    request: DashboardRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    dashboard = Dashboard(
        organization_id=organization_id,
        name=request.name,
        description=request.description,
        layout=request.layout,
        is_public=request.is_public,
        shared_with=[UUID(u) for u in request.shared_with] if request.shared_with else [],
        auto_refresh_seconds=request.auto_refresh_seconds,
        tags=request.tags,
        is_default=request.is_default,
        created_by=user_id,
    )
    created = await service.create_dashboard(dashboard)
    return created.to_dict()


@router.get(
    "/organizations/{organization_id}/dashboards",
    summary="List dashboards",
)
async def list_dashboards(
    organization_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    service: DashboardService = Depends(get_dashboard_service),
) -> list[dict]:
    dashboards = await service.list_dashboards(organization_id)
    return [d.to_dict() for d in dashboards]


@router.get(
    "/organizations/{organization_id}/dashboards/default",
    summary="Get default dashboard",
)
async def get_default_dashboard(
    organization_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    dashboard = await service.get_default_dashboard(organization_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="No default dashboard found")
    return dashboard.to_dict()


@router.get(
    "/organizations/{organization_id}/dashboards/{dashboard_id}",
    summary="Get a dashboard with widgets",
)
async def get_dashboard(
    organization_id: UUID,
    dashboard_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    dashboard = await service.get_dashboard(dashboard_id)
    if not dashboard or dashboard.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard.to_dict()


@router.post(
    "/organizations/{organization_id}/dashboards/{dashboard_id}/widgets",
    status_code=status.HTTP_201_CREATED,
    summary="Add a widget to a dashboard",
)
async def create_widget(
    organization_id: UUID,
    dashboard_id: UUID,
    request: DashboardWidgetRequest,
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    widget = DashboardWidget(
        dashboard_id=dashboard_id,
        widget_type=request.widget_type,
        title=request.title,
        description=request.description,
        metric_names=request.metric_names,
        query=request.query,
        visualization_config=request.visualization_config,
        position_x=request.position_x,
        position_y=request.position_y,
        width=request.width,
        height=request.height,
        time_range_seconds=request.time_range_seconds,
        refresh_interval_seconds=request.refresh_interval_seconds,
        filters=request.filters,
    )
    created = await service.create_widget(widget)
    return created.to_dict()


# --- System Health ---

@router.get(
    "/organizations/{organization_id}/health",
    summary="Get system health report",
)
async def get_system_health(
    organization_id: UUID,
    org_id: UUID = Depends(_require_org_access),
    service: SystemHealthService = Depends(get_system_health_service),
) -> dict:
    return await service.generate_health_report(organization_id)


# --- Batch Operations ---

@router.post(
    "/organizations/{organization_id}/metrics/batch-record",
    summary="Batch record metrics",
)
async def batch_record_metrics(
    organization_id: UUID,
    samples: list[RecordMetricRequest],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_access),
    service: MetricsService = Depends(get_metrics_service),
) -> dict:
    samples_data = [s.model_dump() for s in samples]
    recorded = await service.record_batch(organization_id, samples_data)
    return {"recorded": len(recorded)}


@router.post(
    "/organizations/{organization_id}/alerts/rules/batch",
    summary="Create multiple alert rules",
)
async def batch_create_alert_rules(
    organization_id: UUID,
    requests: list[AlertRuleRequest],
    user_id: UUID = Depends(require_user_id),
    org_id: UUID = Depends(_require_org_admin),
    service: AlertingService = Depends(get_alerting_service),
) -> dict:
    results = []
    for req in requests:
        try:
            rule = AlertRule(
                organization_id=organization_id,
                name=req.name,
                description=req.description,
                source=AlertSource(req.source),
                severity=AlertSeverity(req.severity),
                metric_name=req.metric_name,
                condition=req.condition,
                evaluation_window_seconds=req.evaluation_window_seconds,
                label_matchers=req.label_matchers,
                notification_channels=req.notification_channels,
                auto_resolve=req.auto_resolve,
                resolve_timeout_seconds=req.resolve_timeout_seconds,
                group_by=req.group_by,
                active_hours=req.active_hours,
                tags=req.tags,
            )
            created = await service.create_rule(rule)
            results.append({"name": req.name, "status": "success", "id": str(created.id)})
        except Exception as e:
            results.append({"name": req.name, "status": "error", "error": str(e)})
    return {"processed": len(requests), "results": results}
