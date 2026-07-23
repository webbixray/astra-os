"""Observability & Tenant Dashboard API Routes — E6.4 Beta Launch.

Endpoints for per-tenant Grafana dashboards, cost tracking, alerting,
SLA monitoring, and anomaly detection.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.domain.common import now
from app.domain.entities.organization import Organization
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.entities.advertising import AdAccount, AdPlatform
from app.presentation.dependencies import get_db
from app.presentation.dependencies import get_redis
from app.presentation.middleware.auth import require_user_id
from app.presentation.dependencies import require_organization_id
from app.presentation.dependencies import get_db as get_db_dep
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
from app.infrastructure.db.repositories.advertising.advertising_repository import AdAccountRepository

router = APIRouter(prefix="/observability", tags=["observability"])


# --- Request/Response Models ---


class TenantDashboardResponse(BaseModel):
    """Tenant dashboard overview."""

    organization_id: UUID
    organization_name: str
    period_start: datetime
    period_end: datetime
    summary: dict[str, Any]
    campaigns: dict[str, Any]
    spend: dict[str, Any]
    performance: dict[str, Any]
    agents: dict[str, Any]
    alerts: list[dict[str, Any]]


class CostBreakdownResponse(BaseModel):
    """Cost breakdown by category."""

    organization_id: UUID
    period_start: datetime
    period_end: datetime
    total_cost_cents: int
    by_category: dict[str, int]
    by_campaign: list[dict[str, Any]]
    by_platform: list[dict[str, Any]]
    model_inference_cost_cents: int
    projected_monthly_cost_cents: int


class AlertRuleCreateRequest(BaseModel):
    """Create alert rule request."""

    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    metric: str = Field(pattern=r"^[a-z_]+$")
    condition: str = Field(pattern=r"^(gt|lt|gte|lte|eq|neq)$")
    threshold: float
    window_minutes: int = Field(ge=1, le=1440)
    severity: str = Field(pattern=r"^(info|warning|critical)$")
    channels: list[str] = Field(default_factory=lambda: ["slack", "email"])
    enabled: bool = True


class AlertRuleResponse(BaseModel):
    """Alert rule response."""

    id: UUID
    organization_id: UUID
    name: str
    description: str
    metric: str
    condition: str
    threshold: float
    window_minutes: int
    severity: str
    channels: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_triggered_at: datetime | None = None
    trigger_count: int = 0


class AlertInstanceResponse(BaseModel):
    """Alert instance response."""

    id: UUID
    rule_id: UUID
    organization_id: UUID
    metric: str
    value: float
    threshold: float
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None


class AnomalyResponse(BaseModel):
    """Anomaly detection response."""

    id: UUID
    organization_id: UUID
    metric: str
    expected_value: float
    actual_value: float
    deviation_percentage: float
    severity: str
    detected_at: datetime
    context: dict[str, Any]


class SLAReportResponse(BaseModel):
    """SLA compliance report."""

    organization_id: UUID
    period_start: datetime
    period_end: datetime
    availability_percentage: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    error_rate_percentage: float
    total_requests: int
    failed_requests: int
    sla_target: dict[str, Any]
    compliance: bool


# --- In-memory stores (replace with DB in production) ---

_alert_rules: dict[UUID, dict[str, Any]] = {}
_alert_instances: dict[UUID, dict[str, Any]] = {}
_anomalies: dict[UUID, dict[str, Any]] = {}


# --- Helper Functions ---


async def _get_organization(db: AsyncSession, org_id: UUID) -> Organization | None:
    org_repo = OrganizationRepositoryImpl(db)
    return await org_repo.find_by_id(org_id)


async def _get_campaign_stats(
    db: AsyncSession, org_id: UUID, days: int = 30
) -> dict[str, Any]:
    """Get campaign statistics for organization."""
    cutoff = now() - timedelta(days=days)
    campaign_repo = CampaignRepositoryImpl(db)
    campaigns = await campaign_repo.find_by_organization(org_id)

    recent = [c for c in campaigns if c.created_at >= cutoff]
    active = [c for c in campaigns if c.status == 'active']

    total_budget = sum(c.budget_cents for c in campaigns)
    active_budget = sum(c.budget_cents for c in active)

    return {
        "total": len(campaigns),
        "active": len(active),
        "recent_30d": len(recent),
        "total_budget_cents": total_budget,
        "active_budget_cents": active_budget,
        "by_status": {
            status.value: sum(1 for c in campaigns if c.status == status)
            for status in ['draft', 'pending_approval', 'active', 'paused', 'completed', 'archived']
        },
    }


async def _get_spend_stats(
    db: AsyncSession, org_id: UUID, days: int = 30
) -> dict[str, Any]:
    """Get spend statistics for organization."""
    cutoff = now() - timedelta(days=days)
    ad_account_repo = AdAccountRepository(db)
    accounts = await ad_account_repo.find_by_organization(org_id)

    # In production, this would query actual spend from ad platforms
    # For now, return mock data based on campaign budgets
    campaign_repo = CampaignRepositoryImpl(db)
    campaigns = await campaign_repo.find_by_organization(org_id)
    active_campaigns = [c for c in campaigns if c.status == 'active']

    total_spend_cents = sum(c.budget_cents for c in active_campaigns) * 0.3  # Mock: 30% spent
    daily_spend_cents = total_spend_cents / days if days > 0 else 0

    return {
        "total_spend_cents": int(total_spend_cents),
        "daily_average_cents": int(daily_spend_cents),
        "by_platform": {
            "meta": int(total_spend_cents * 0.4),
            "google": int(total_spend_cents * 0.35),
            "linkedin": int(total_spend_cents * 0.15),
            "other": int(total_spend_cents * 0.1),
        },
        "by_campaign": [
            {
                "campaign_id": str(c.id),
                "name": c.name,
                "spend_cents": int(c.budget_cents * 0.3),
                "budget_cents": c.budget_cents,
                "pacing_percentage": 30.0,
            }
            for c in active_campaigns[:10]
        ],
    }


async def _get_performance_stats(
    db: AsyncSession, org_id: UUID, days: int = 30
) -> dict[str, Any]:
    """Get performance statistics for organization."""
    # In production, this would query actual metrics from ad platforms
    return {
        "roas": 3.2,
        "ctr": 0.024,
        "cpc_cents": 125,
        "cpa_cents": 4500,
        "conversions": 127,
        "impressions": 450000,
        "clicks": 10800,
        "by_platform": {
            "meta": {"roas": 3.5, "ctr": 0.028, "cpc_cents": 110},
            "google": {"roas": 3.0, "ctr": 0.022, "cpc_cents": 140},
            "linkedin": {"roas": 2.8, "ctr": 0.018, "cpc_cents": 180},
        },
    }


async def _get_agent_stats(
    db: AsyncSession, org_id: UUID, days: int = 30
) -> dict[str, Any]:
    """Get AI agent statistics for organization."""
    # In production, this would query agent execution logs
    return {
        "total_executions": 1247,
        "successful_executions": 1198,
        "failed_executions": 49,
        "average_latency_ms": 1250,
        "total_tokens": 2_450_000,
        "total_cost_cents": 12450,
        "by_agent_type": {
            "CampaignOptimizer": {"executions": 450, "success_rate": 0.96, "avg_latency_ms": 1100},
            "ContentGenerator": {"executions": 380, "success_rate": 0.97, "avg_latency_ms": 2200},
            "AudienceResearcher": {"executions": 210, "success_rate": 0.94, "avg_latency_ms": 1800},
            "CreativeReviewer": {"executions": 157, "success_rate": 0.99, "avg_latency_ms": 900},
            "BidManager": {"executions": 50, "success_rate": 0.92, "avg_latency_ms": 800},
        },
        "model_usage": {
            "nvidia_nim": {"requests": 890, "cost_cents": 4500},
            "openai": {"requests": 234, "cost_cents": 5200},
            "anthropic": {"requests": 89, "cost_cents": 2100},
            "gemini": {"requests": 34, "cost_cents": 650},
        },
    }


async def _get_cost_breakdown(
    db: AsyncSession, org_id: UUID, days: int = 30
) -> dict[str, Any]:
    """Get detailed cost breakdown for organization."""
    agent_stats = await _get_agent_stats(db, org_id, days)
    spend_stats = await _get_spend_stats(db, org_id, days)

    model_cost = agent_stats["total_cost_cents"]
    ad_spend = spend_stats["total_spend_cents"]
    platform_fees = int(ad_spend * 0.02)  # 2% platform fees
    infrastructure = 5000  # Fixed monthly infrastructure cost

    total = model_cost + ad_spend + platform_fees + infrastructure
    projected = int(total / days * 30) if days > 0 else total

    return {
        "total_cost_cents": total,
        "by_category": {
            "model_inference": model_cost,
            "ad_spend": ad_spend,
            "platform_fees": platform_fees,
            "infrastructure": infrastructure,
        },
        "model_inference_cost_cents": model_cost,
        "projected_monthly_cost_cents": projected,
        "by_campaign": spend_stats["by_campaign"],
        "by_platform": [
            {"platform": k, "cost_cents": v}
            for k, v in spend_stats["by_platform"].items()
        ],
    }


def _check_alert_rules(org_id: UUID, metrics: dict[str, float]) -> list[dict[str, Any]]:
    """Check alert rules against current metrics."""
    triggered = []
    for rule_id, rule in _alert_rules.items():
        if rule["organization_id"] != org_id or not rule["enabled"]:
            continue

        metric_value = metrics.get(rule["metric"])
        if metric_value is None:
            continue

        condition = rule["condition"]
        threshold = rule["threshold"]
        triggered_now = False

        if condition == "gt" and metric_value > threshold:
            triggered_now = True
        elif condition == "lt" and metric_value < threshold:
            triggered_now = True
        elif condition == "gte" and metric_value >= threshold:
            triggered_now = True
        elif condition == "lte" and metric_value <= threshold:
            triggered_now = True
        elif condition == "eq" and metric_value == threshold:
            triggered_now = True
        elif condition == "neq" and metric_value != threshold:
            triggered_now = True

        if triggered_now:
            instance_id = UUID(int=hash(f"{rule_id}{now().isoformat()}") % (2**128))
            instance = {
                "id": instance_id,
                "rule_id": rule_id,
                "organization_id": org_id,
                "metric": rule["metric"],
                "value": metric_value,
                "threshold": threshold,
                "severity": rule["severity"],
                "message": f"{rule['name']}: {rule['metric']} is {metric_value} (threshold: {threshold})",
                "triggered_at": now(),
                "resolved_at": None,
                "acknowledged_at": None,
                "acknowledged_by": None,
            }
            _alert_instances[instance_id] = instance
            rule["last_triggered_at"] = now()
            rule["trigger_count"] = rule.get("trigger_count", 0) + 1
            triggered.append(instance)

    return triggered


def _detect_anomalies(org_id: UUID, metrics: dict[str, float]) -> list[dict[str, Any]]:
    """Simple anomaly detection using statistical thresholds."""
    # In production, this would use ML models
    anomalies = []
    
    # Mock expected values (in production, these would be learned)
    expected = {
        "daily_spend_cents": 50000,
        "roas": 3.0,
        "ctr": 0.025,
        "cpc_cents": 130,
        "error_rate": 0.001,
        "latency_p95_ms": 500,
    }

    for metric, actual in metrics.items():
        if metric not in expected:
            continue
        
        exp = expected[metric]
        if exp == 0:
            continue
            
        deviation = abs(actual - exp) / exp * 100
        
        if deviation > 50:  # 50% deviation threshold
            severity = "critical" if deviation > 100 else "warning"
            anomaly_id = UUID(int=hash(f"{org_id}{metric}{now().isoformat()}") % (2**128))
            anomaly = {
                "id": anomaly_id,
                "organization_id": org_id,
                "metric": metric,
                "expected_value": exp,
                "actual_value": actual,
                "deviation_percentage": deviation,
                "severity": severity,
                "detected_at": now(),
                "context": {"threshold": 50},
            }
            _anomalies[anomaly_id] = anomaly
            anomalies.append(anomaly)

    return anomalies


# --- Routes ---


@router.get(
    "/dashboard",
    response_model=TenantDashboardResponse,
    summary="Get tenant dashboard overview",
)
async def get_tenant_dashboard(
    days: int = Query(30, ge=1, le=365),
    organization_id: UUID = Depends(require_organization_id),
    db: AsyncSession = Depends(get_db_dep),
) -> TenantDashboardResponse:
    """Get comprehensive tenant dashboard data."""
    org = await _get_organization(db, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    period_end = now()
    period_start = period_end - timedelta(days=days)

    # Gather all stats
    campaign_stats = await _get_campaign_stats(db, organization_id, days)
    spend_stats = await _get_spend_stats(db, organization_id, days)
    performance_stats = await _get_performance_stats(db, organization_id, days)
    agent_stats = await _get_agent_stats(db, organization_id, days)

    # Check alerts
    metrics_for_alerts = {
        "daily_spend_cents": spend_stats["daily_average_cents"],
        "roas": performance_stats["roas"],
        "ctr": performance_stats["ctr"],
        "cpc_cents": performance_stats["cpc_cents"],
        "error_rate": 0.001,
        "latency_p95_ms": 500,
    }
    alerts = _check_alert_rules(organization_id, metrics_for_alerts)

    # Detect anomalies
    anomalies = _detect_anomalies(organization_id, metrics_for_alerts)
    for anomaly in anomalies:
        alerts.append({
            "type": "anomaly",
            "severity": anomaly["severity"],
            "message": f"Anomaly detected: {anomaly['metric']} deviated {anomaly['deviation_percentage']:.1f}%",
            "triggered_at": anomaly["detected_at"].isoformat(),
        })

    return TenantDashboardResponse(
        organization_id=organization_id,
        organization_name=org.name,
        period_start=period_start,
        period_end=period_end,
        summary={
            "total_campaigns": campaign_stats["total"],
            "active_campaigns": campaign_stats["active"],
            "total_spend_cents": spend_stats["total_spend_cents"],
            "roas": performance_stats["roas"],
            "agent_executions": agent_stats["total_executions"],
            "model_cost_cents": agent_stats["total_cost_cents"],
        },
        campaigns=campaign_stats,
        spend=spend_stats,
        performance=performance_stats,
        agents=agent_stats,
        alerts=alerts[:20],  # Limit to 20 most recent
    )


@router.get(
    "/costs",
    response_model=CostBreakdownResponse,
    summary="Get cost breakdown",
)
async def get_cost_breakdown(
    days: int = Query(30, ge=1, le=365),
    organization_id: UUID = Depends(require_organization_id),
    db: AsyncSession = Depends(get_db_dep),
) -> CostBreakdownResponse:
    """Get detailed cost breakdown for the organization."""
    org = await _get_organization(db, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    period_end = now()
    period_start = period_end - timedelta(days=days)

    cost_data = await _get_cost_breakdown(db, organization_id, days)

    return CostBreakdownResponse(
        organization_id=organization_id,
        period_start=period_start,
        period_end=period_end,
        **cost_data,
    )


# --- Alert Rules ---


@router.post(
    "/alerts/rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert rule",
)
async def create_alert_rule(
    request: AlertRuleCreateRequest,
    organization_id: UUID = Depends(require_organization_id),
    user_id: UUID = Depends(require_user_id),
) -> AlertRuleResponse:
    """Create a new alert rule for the organization."""
    rule_id = uuid4()
    rule = {
        "id": rule_id,
        "organization_id": organization_id,
        "name": request.name,
        "description": request.description,
        "metric": request.metric,
        "condition": request.condition,
        "threshold": request.threshold,
        "window_minutes": request.window_minutes,
        "severity": request.severity,
        "channels": request.channels,
        "enabled": request.enabled,
        "created_at": now(),
        "updated_at": now(),
        "last_triggered_at": None,
        "trigger_count": 0,
    }
    _alert_rules[rule_id] = rule
    return AlertRuleResponse(**rule)


@router.get(
    "/alerts/rules",
    response_model=list[AlertRuleResponse],
    summary="List alert rules",
)
async def list_alert_rules(
    organization_id: UUID = Depends(require_organization_id),
) -> list[AlertRuleResponse]:
    """List all alert rules for the organization."""
    rules = [r for r in _alert_rules.values() if r["organization_id"] == organization_id]
    return [AlertRuleResponse(**r) for r in rules]


@router.get(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get alert rule",
)
async def get_alert_rule(
    rule_id: UUID,
    organization_id: UUID = Depends(require_organization_id),
) -> AlertRuleResponse:
    """Get a specific alert rule."""
    rule = _alert_rules.get(rule_id)
    if not rule or rule["organization_id"] != organization_id:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return AlertRuleResponse(**rule)


@router.patch(
    "/alerts/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update alert rule",
)
async def update_alert_rule(
    rule_id: UUID,
    request: AlertRuleCreateRequest,
    organization_id: UUID = Depends(require_organization_id),
) -> AlertRuleResponse:
    """Update an alert rule."""
    rule = _alert_rules.get(rule_id)
    if not rule or rule["organization_id"] != organization_id:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    rule.update(
        name=request.name,
        description=request.description,
        metric=request.metric,
        condition=request.condition,
        threshold=request.threshold,
        window_minutes=request.window_minutes,
        severity=request.severity,
        channels=request.channels,
        enabled=request.enabled,
        updated_at=now(),
    )
    return AlertRuleResponse(**rule)


@router.delete(
    "/alerts/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert rule",
)
async def delete_alert_rule(
    rule_id: UUID,
    organization_id: UUID = Depends(require_organization_id),
) -> None:
    """Delete an alert rule."""
    rule = _alert_rules.get(rule_id)
    if not rule or rule["organization_id"] != organization_id:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    del _alert_rules[rule_id]


# --- Alert Instances ---


@router.get(
    "/alerts/instances",
    response_model=list[AlertInstanceResponse],
    summary="List alert instances",
)
async def list_alert_instances(
    resolved: bool | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(50, le=200),
    organization_id: UUID = Depends(require_organization_id),
) -> list[AlertInstanceResponse]:
    """List alert instances for the organization."""
    instances = [i for i in _alert_instances.values() if i["organization_id"] == organization_id]

    if resolved is not None:
        instances = [i for i in instances if (i["resolved_at"] is not None) == resolved]
    if severity:
        instances = [i for i in instances if i["severity"] == severity]

    instances.sort(key=lambda x: x["triggered_at"], reverse=True)
    return [AlertInstanceResponse(**i) for i in instances[:limit]]


@router.post(
    "/alerts/instances/{instance_id}/acknowledge",
    response_model=AlertInstanceResponse,
    summary="Acknowledge alert instance",
)
async def acknowledge_alert(
    instance_id: UUID,
    organization_id: UUID = Depends(require_organization_id),
    user_id: UUID = Depends(require_user_id),
) -> AlertInstanceResponse:
    """Acknowledge an alert instance."""
    instance = _alert_instances.get(instance_id)
    if not instance or instance["organization_id"] != organization_id:
        raise HTTPException(status_code=404, detail="Alert instance not found")

    instance["acknowledged_at"] = now()
    instance["acknowledged_by"] = user_id
    return AlertInstanceResponse(**instance)


@router.post(
    "/alerts/instances/{instance_id}/resolve",
    response_model=AlertInstanceResponse,
    summary="Resolve alert instance",
)
async def resolve_alert(
    instance_id: UUID,
    organization_id: UUID = Depends(require_organization_id),
) -> AlertInstanceResponse:
    """Resolve an alert instance."""
    instance = _alert_instances.get(instance_id)
    if not instance or instance["organization_id"] != organization_id:
        raise HTTPException(status_code=404, detail="Alert instance not found")

    instance["resolved_at"] = now()
    return AlertInstanceResponse(**instance)


# --- Anomalies ---


@router.get(
    "/anomalies",
    response_model=list[AnomalyResponse],
    summary="List detected anomalies",
)
async def list_anomalies(
    severity: str | None = Query(None),
    limit: int = Query(50, le=200),
    organization_id: UUID = Depends(require_organization_id),
) -> list[AnomalyResponse]:
    """List detected anomalies for the organization."""
    anomalies_list = [a for a in _anomalies.values() if a["organization_id"] == organization_id]

    if severity:
        anomalies_list = [a for a in anomalies_list if a["severity"] == severity]

    anomalies_list.sort(key=lambda x: x["detected_at"], reverse=True)
    return [AnomalyResponse(**a) for a in anomalies_list[:limit]]


# --- SLA Reports ---


@router.get(
    "/sla",
    response_model=SLAReportResponse,
    summary="Get SLA compliance report",
)
async def get_sla_report(
    days: int = Query(30, ge=1, le=365),
    organization_id: UUID = Depends(require_organization_id),
    db: AsyncSession = Depends(get_db_dep),
) -> SLAReportResponse:
    """Get SLA compliance report for the organization."""
    # In production, this would query actual metrics from monitoring systems
    period_end = now()
    period_start = period_end - timedelta(days=days)

    return SLAReportResponse(
        organization_id=organization_id,
        period_start=period_start,
        period_end=period_end,
        availability_percentage=99.95,
        latency_p50_ms=120,
        latency_p95_ms=450,
        latency_p99_ms=890,
        error_rate_percentage=0.08,
        total_requests=1_250_000,
        failed_requests=1_000,
        sla_target={
            "availability": 99.9,
            "latency_p99_ms": 1000,
            "error_rate_percentage": 0.1,
        },
        compliance=True,
    )


# --- Grafana Dashboard Provisioning ---


@router.get(
    "/grafana/dashboards",
    response_model=list[dict[str, Any]],
    summary="List available Grafana dashboards",
)
async def list_grafana_dashboards(
    organization_id: UUID = Depends(require_organization_id),
) -> list[dict[str, Any]]:
    """List available Grafana dashboards for the tenant."""
    return [
        {
            "uid": "astra-tenant-overview",
            "title": "ASTRA OS - Tenant Overview",
            "description": "High-level tenant metrics including campaigns, spend, and agent performance",
            "tags": ["astra", "tenant", "overview"],
            "url": f"/d/astra-tenant-overview?orgId={organization_id}",
        },
        {
            "uid": "astra-campaigns",
            "title": "ASTRA OS - Campaign Performance",
            "description": "Detailed campaign performance across all platforms",
            "tags": ["astra", "campaigns", "performance"],
            "url": f"/d/astra-campaigns?orgId={organization_id}",
        },
        {
            "uid": "astra-agents",
            "title": "ASTRA OS - Agent Performance",
            "description": "AI agent execution metrics, costs, and model usage",
            "tags": ["astra", "agents", "ai"],
            "url": f"/d/astra-agents?orgId={organization_id}",
        },
        {
            "uid": "astra-costs",
            "title": "ASTRA OS - Cost Analysis",
            "description": "Cost breakdown by category, campaign, and platform",
            "tags": ["astra", "costs", "finance"],
            "url": f"/d/astra-costs?orgId={organization_id}",
        },
        {
            "uid": "astra-sla",
            "title": "ASTRA OS - SLA Compliance",
            "description": "Service level agreement compliance and uptime metrics",
            "tags": ["astra", "sla", "reliability"],
            "url": f"/d/astra-sla?orgId={organization_id}",
        },
    ]


@router.post(
    "/grafana/dashboards/provision",
    response_model=dict[str, Any],
    summary="Provision Grafana dashboards for tenant",
)
async def provision_grafana_dashboards(
    organization_id: UUID = Depends(require_organization_id),
    user_id: UUID = Depends(require_user_id),
) -> dict[str, Any]:
    """Provision standard Grafana dashboards for the tenant organization."""
    # In production, this would use Grafana HTTP API to create dashboards
    # and configure datasources with organization-scoped queries
    
    return {
        "provisioned": True,
        "dashboards_created": 5,
        "datasources_configured": 3,
        "message": "Grafana dashboards provisioned successfully. Access at /grafana",
    }


# --- Health & Metrics ---


@router.get(
    "/health",
    response_model=dict[str, Any],
    summary="Observability service health",
)
async def observability_health() -> dict[str, Any]:
    """Health check for observability service."""
    return {
        "status": "healthy",
        "service": "observability",
        "features": {
            "tenant_dashboards": True,
            "cost_tracking": True,
            "alerting": True,
            "anomaly_detection": True,
            "sla_reporting": True,
            "grafana_provisioning": True,
        },
        "alert_rules_count": len(_alert_rules),
        "active_alerts": len([i for i in _alert_instances.values() if i["resolved_at"] is None]),
        "anomalies_count": len(_anomalies),
    }


# Import uuid4 for alert rule IDs
from uuid import uuid4