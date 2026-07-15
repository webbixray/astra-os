"""SLO/SLI definitions for Astra OS."""

from dataclasses import dataclass
from typing import Any


@dataclass
class SLIDefinition:
    """Service Level Indicator definition."""

    name: str
    description: str
    promql: str
    target: float
    window: str
    severity: str = "critical"


# SLO Definitions
SLO_DEFINITIONS: dict[str, SLIDefinition] = {
    "agent_availability": SLIDefinition(
        name="agent_availability",
        description="Agent runs complete successfully",
        promql='sum(rate(agent_runs_total{success="true"}[5m])) / sum(rate(agent_runs_total[5m]))',
        target=0.999,  # 99.9%
        window="30d",
        severity="critical",
    ),
    "agent_latency_p95": SLIDefinition(
        name="agent_latency_p95",
        description="P95 agent run latency",
        promql="histogram_quantile(0.95, rate(agent_duration_seconds_bucket[5m]))",
        target=30.0,  # 30 seconds
        window="30d",
        severity="critical",
    ),
    "agent_latency_p99": SLIDefinition(
        name="agent_latency_p99",
        description="P99 agent run latency",
        promql="histogram_quantile(0.99, rate(agent_duration_seconds_bucket[5m]))",
        target=60.0,  # 60 seconds
        window="30d",
        severity="warning",
    ),
    "tool_call_success_rate": SLIDefinition(
        name="tool_call_success_rate",
        description="Tool calls succeed",
        promql='sum(rate(agent_tool_calls_total{success="true"}[5m])) / sum(rate(agent_tool_calls_total[5m]))',
        target=0.995,  # 99.5%
        window="30d",
        severity="critical",
    ),
    "delegation_success_rate": SLIDefinition(
        name="delegation_success_rate",
        description="Agent delegations succeed",
        promql='sum(rate(agent_delegations_total{success="true"}[5m])) / sum(rate(agent_delegations_total[5m]))',
        target=0.99,  # 99%
        window="30d",
        severity="critical",
    ),
    "dlq_depth": SLIDefinition(
        name="dlq_depth",
        description="DLQ doesn't accumulate beyond threshold",
        promql="astra_dlq_pending",
        target=100,  # Max 100 messages
        window="5m",
        severity="warning",
    ),
    "dlq_growth_rate": SLIDefinition(
        name="dlq_growth_rate",
        description="DLQ growth rate is controlled",
        promql="rate(astra_dlq_pending[5m])",
        target=10,  # Max 10 messages/sec growth
        window="5m",
        severity="warning",
    ),
    "circuit_breaker_closed": SLIDefinition(
        name="circuit_breaker_closed",
        description="Circuit breakers stay closed",
        promql='sum(circuit_breaker_state{state="closed"}) / (sum(circuit_breaker_state{state="closed"}) + sum(circuit_breaker_state{state="open"}))',
        target=0.99,  # 99% time closed
        window="30d",
        severity="critical",
    ),
    "circuit_breaker_half_open_success": SLIDefinition(
        name="circuit_breaker_half_open_success",
        description="Half-open probes succeed",
        promql='sum(rate(circuit_breaker_calls_total{state="half_open",result="success"}[5m])) / sum(rate(circuit_breaker_calls_total{state="half_open"}[5m]))',
        target=0.8,  # 80% success in half-open
        window="5m",
        severity="warning",
    ),
    "ai_provider_availability": SLIDefinition(
        name="ai_provider_availability",
        description="AI providers are available (not circuit open)",
        promql='sum(circuit_breaker_state{state="closed",name=~"nvidia_nim|openai|anthropic|gemini"}) / sum(circuit_breaker_state{name=~"nvidia_nim|openai|anthropic|gemini"})',
        target=0.95,  # 95% of providers available
        window="30d",
        severity="critical",
    ),
    "cost_burn_rate": SLIDefinition(
        name="cost_burn_rate",
        description="Monthly cost projection within budget",
        promql="sum(rate(agent_cost_usd_total[1h])) * 24 * 30",
        target=50000.0,  # $50k/month max
        window="1h",
        severity="warning",
    ),
    "agent_task_retry_rate": SLIDefinition(
        name="agent_task_retry_rate",
        description="Agent task retries are minimal",
        promql="rate(astra_dlq_added_total[5m]) / rate(astra_tasks_started_total[5m])",
        target=0.05,  # < 5% tasks go to DLQ
        window="5m",
        severity="warning",
    ),
}


def get_all_slos() -> dict[str, SLIDefinition]:
    """Get all SLO definitions."""
    return SLO_DEFINITIONS


def get_slo_config() -> dict[str, Any]:
    """Get SLO configuration for Grafana/Alertmanager."""
    return {
        name: {
            "description": slo.description,
            "promql": slo.promql,
            "target": slo.target,
            "window": slo.window,
            "severity": slo.severity,
        }
        for name, slo in SLO_DEFINITIONS.items()
    }


def get_burn_rate_configs() -> dict[str, dict[str, Any]]:
    """Get multi-window burn rate alert configurations."""
    return {
        "agent_availability": {
            "slo": "agent_availability",
            "target": 0.999,
            "windows": [
                {"window": "5m", "threshold": 10, "severity": "critical", "name": "fast"},
                {"window": "1h", "threshold": 2, "severity": "critical", "name": "medium"},
                {"window": "6h", "threshold": 0.5, "severity": "warning", "name": "slow"},
            ],
        },
        "tool_call_success_rate": {
            "slo": "tool_call_success_rate",
            "target": 0.995,
            "windows": [
                {"window": "5m", "threshold": 10, "severity": "critical", "name": "fast"},
                {"window": "1h", "threshold": 2, "severity": "critical", "name": "medium"},
                {"window": "6h", "threshold": 0.5, "severity": "warning", "name": "slow"},
            ],
        },
        "delegation_success_rate": {
            "slo": "delegation_success_rate",
            "target": 0.99,
            "windows": [
                {"window": "5m", "threshold": 10, "severity": "critical", "name": "fast"},
                {"window": "1h", "threshold": 2, "severity": "critical", "name": "medium"},
                {"window": "6h", "threshold": 0.5, "severity": "warning", "name": "slow"},
            ],
        },
        "dlq_depth": {
            "slo": "dlq_depth",
            "target": 100,
            "windows": [
                {"window": "2m", "threshold": 12, "severity": "critical", "name": "fast"},
                {"window": "15m", "threshold": 2, "severity": "warning", "name": "medium"},
                {"window": "1h", "threshold": 0.5, "severity": "warning", "name": "slow"},
            ],
        },
        "circuit_breaker_closed": {
            "slo": "circuit_breaker_closed",
            "target": 0.99,
            "windows": [
                {"window": "2m", "threshold": 12, "severity": "critical", "name": "fast"},
                {"window": "15m", "threshold": 2, "severity": "warning", "name": "medium"},
                {"window": "1h", "threshold": 0.5, "severity": "warning", "name": "slow"},
            ],
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_slo_config(), indent=2))
