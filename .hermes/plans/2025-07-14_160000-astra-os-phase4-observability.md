# ASTRA OS — Phase 4: Observability Polish Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task = 2-5 min focused work. TDD enforced. Independent reviewer subagent after each task.

**Goal:** Production-grade observability with Grafana dashboards, SLOs, cost tracking, and distributed tracing visualization.

**Architecture:** Clean Architecture + DDD. Target: `services/agent_orchestrator/` + `apps/api/` + Grafana provisioning

**Tech Stack:** Python 3.12, OpenTelemetry, Prometheus, Grafana, Loki, Tempo, pytest

---

## Phase 4A: Enhanced OTel Spans & Attributes

### Task 4.1: Add Semantic Conventions to Agent Spans

**Objective:** Enrich agent spans with standard OTel semantic conventions for better querying in Tempo/Grafana.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_agent_semantic_conventions.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from services.agent_orchestrator.agent import Agent, AgentConfig, AgentType, AgentContext, AgentResult

@pytest.fixture
def agent_config():
    return AgentConfig(
        agent_id=uuid4(),
        agent_type=AgentType.CEO,
        name="Test CEO",
        autonomy_level=1,
    )

@pytest.fixture
def mock_context():
    return AgentContext(
        agent_id=uuid4(),
        tenant_id=uuid4(),
    )

@pytest.mark.asyncio
async def test_agent_run_span_has_semantic_attributes(agent_config, mock_context):
    """Agent run span should have standard semantic conventions."""
    agent = Agent(agent_config, agent_config.tenant_id)

    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        agent.execute = AsyncMock(return_value=AgentResult(
            agent_id=agent_config.agent_id,
            success=True,
            duration_ms=150,
            tokens_used=100,
            cost_usd=0.001,
            iterations=1,
        ))

        await agent.run(mock_context, {"task": "test"})

        # Check semantic conventions
        mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
        mock_span.set_attribute.assert_any_call("agent.astra.type", "CEO")
        mock_span.set_attribute.assert_any_call("agent.astra.tenant_id", str(mock_context.tenant_id))
        mock_span.set_attribute.assert_any_call("agent.astra.session_id", str(mock_context.session_id))
        mock_span.set_attribute.assert_any_call("agent.astra.autonomy_level", 1)

@pytest.mark.asyncio
async def test_tool_call_span_has_semantic_attributes(agent_config, mock_context):
    """Tool call span should have standard semantic conventions."""
    agent = Agent(agent_config, agent_config.tenant_id)

    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        agent.tool_registry.execute_tool = AsyncMock(return_value={
            "success": True,
            "result": "output",
        })

        await agent.call_tool("web_search", {"query": "test"}, mock_context)

        # Check semantic conventions
        mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
        mock_span.set_attribute.assert_any_call("tool.name", "web_search")
        mock_span.set_attribute.assert_any_call("tool.astra.agent_type", "CEO")
        mock_span.set_attribute.assert_any_call("tool.astra.agent_id", str(agent_config.agent_id))

@pytest.mark.asyncio
async def test_delegation_span_has_semantic_attributes(agent_config, mock_context):
    """Delegation span should have standard semantic conventions."""
    agent = Agent(agent_config, agent_config.tenant_id)

    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        # Mock subagent
        with patch("services.agent_orchestrator.agent.get_agent_registry") as mock_registry:
            mock_subagent = AsyncMock()
            mock_subagent.agent_id = uuid4()
            mock_subagent.agent_type = AgentType.CONTENT_SPECIALIST
            mock_subagent.run = AsyncMock(return_value=AgentResult(
                agent_id=mock_subagent.agent_id,
                success=True,
                duration_ms=100,
            ))
            mock_registry.return_value.create_agent.return_value = mock_subagent

            await agent.delegate_to_subagent(AgentType.CONTENT_SPECIALIST, {"task": "write"}, mock_context)

            # Check semantic conventions
            mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
            mock_span.set_attribute.assert_any_call("agent.astra.delegation.target_type", "CONTENT_SPECIALIST")
            mock_span.set_attribute.assert_any_call("agent.astra.delegation.target_id", str(mock_subagent.agent_id))
            mock_span.set_attribute.assert_any_call("agent.astra.delegation.parent_id", str(agent_config.agent_id))
```

---

### Task 4.2: Add Span Events for Key Lifecycle Moments

**Objective:** Add span events for governance decisions, approvals, retries, etc.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

```python
# In call_tool() governance check:
if check_result.blocked:
    span.add_event("governance.blocked", {
        "tool.name": tool_name,
        "reason": check_result.reason,
        "autonomy_level": self.config.autonomy_level,
    })

# In call_tool() approval required:
if check_result.requires_approval:
    span.add_event("governance.approval_required", {
        "tool.name": tool_name,
        "reason": check_result.reason,
    })

# In delegate_to_subagent():
span.add_event("agent.delegation.started", {
    "target_type": subagent_type.value,
    "target_id": str(subagent.agent_id),
})
```

---

## Phase 4B: Grafana Dashboard Provisioning

### Task 4.3: Agent Performance Dashboard

**Objective:** Create Grafana dashboard for agent run metrics.

**Files:**
- Create: `docker/monitoring/grafana/dashboards/agent-performance.json`
- Modify: `docker/monitoring/grafana/provisioning/dashboards/dashboards.yml`

**Dashboard Panels:**

| Panel | Query | Visualization |
|-------|-------|---------------|
| Agent Runs/sec | `rate(agent_runs_total[5m])` | Time series |
| Success Rate | `sum(rate(agent_runs_total{success="true"}[5m])) / sum(rate(agent_runs_total[5m]))` | Stat |
| P95 Duration | `histogram_quantile(0.95, rate(agent_duration_seconds_bucket[5m]))` | Time series |
| Active Agents | `agent_active_count` | Time series |
| Tokens/sec | `rate(agent_tokens_total[5m])` | Time series |
| Cost/sec | `rate(agent_cost_usd_total[5m])` | Time series |
| Tool Calls/sec | `rate(agent_tool_calls_total[5m])` | Time series |
| Delegations/sec | `rate(agent_delegations_total[5m])` | Time series |

**Grouped by:** `agent_type`

---

### Task 4.4: Circuit Breaker Dashboard

**Objective:** Dashboard for monitoring circuit breaker states.

**Files:**
- Create: `docker/monitoring/grafana/dashboards/circuit-breakers.json`

**Panels:**

| Panel | Query | Visualization |
|-------|-------|---------------|
| Circuit States | `circuit_breaker_state` | State timeline |
| Calls Total | `rate(circuit_breaker_calls_total[5m])` | Time series by result |
| Open Circuits | `circuit_breaker_state{state="open"} == 1` | Table |
| Half-Open Probes | `rate(circuit_breaker_calls_total{result="success"}[5m])` | Time series |

**Alert Rules (in dashboard):**
- Any circuit OPEN > 1m → Critical
- Circuit HALF_OPEN > 5m → Warning

---

### Task 4.5: DLQ Dashboard

**Objective:** Dashboard for dead letter queue monitoring.

**Files:**
- Create: `docker/monitoring/grafana/dashboards/dlq-monitoring.json`

**Panels:**

| Panel | Query | Visualization |
|-------|-------|---------------|
| DLQ Depth | `astra_dlq_pending` | Time series |
| DLQ Growth Rate | `rate(astra_dlq_pending[5m])` | Time series |
| Replayed Total | `astra_dlq_replayed_total` | Stat |
| Retry Outcomes | `rate(agent_task_retries_total[5m])` | Time series |
| Top Failed Streams | `topk(10, astra_dlq_pending by (stream))` | Table |

---

### Task 4.6: Cost Tracking Dashboard

**Objective:** Dashboard for AI cost tracking across providers.

**Files:**
- Create: `docker/monitoring/grafana/dashboards/cost-tracking.json`

**Panels:**

| Panel | Query | Visualization |
|-------|-------|---------------|
| Cost/sec | `rate(agent_cost_usd_total[5m])` | Time series by agent_type |
| Daily Cost | `sum(increase(agent_cost_usd_total[1d]))` | Bar chart by day |
| Cost by Provider | `sum(rate(ai_provider_cost_usd_total[5m])) by (provider)` | Pie chart |
| Cost per 1K Tokens | `rate(agent_cost_usd_total[5m]) / rate(agent_tokens_total[5m]) * 1000` | Time series |
| Budget Burn Rate | `sum(rate(agent_cost_usd_total[1h])) * 24 * 30` | Stat (monthly projection) |

---

## Phase 4C: SLO/SLI Definitions

### Task 4.7: Define SLOs in Code

**Objective:** Codify SLOs for alerting and dashboarding.

**Files:**
- Create: `services/agent_orchestrator/slo.py`

```python
"""SLO/SLI definitions for Astra OS."""

SLO_DEFINITIONS = {
    "agent_availability": {
        "description": "Agent runs complete successfully",
        "sli": "sum(rate(agent_runs_total{success='true'}[5m])) / sum(rate(agent_runs_total[5m]))",
        "target": 0.999,  # 99.9%
        "window": "30d",
    },
    "agent_latency_p95": {
        "description": "P95 agent run latency",
        "sli": "histogram_quantile(0.95, rate(agent_duration_seconds_bucket[5m]))",
        "target": 30.0,  # 30 seconds
        "window": "30d",
    },
    "tool_call_success_rate": {
        "description": "Tool calls succeed",
        "sli": "sum(rate(agent_tool_calls_total{success='true'}[5m])) / sum(rate(agent_tool_calls_total[5m]))",
        "target": 0.995,  # 99.5%
        "window": "30d",
    },
    "dlq_depth": {
        "description": "DLQ doesn't accumulate",
        "sli": "astra_dlq_pending",
        "target": 100,  # Max 100 messages
        "window": "5m",
    },
    "circuit_breaker_closed": {
        "description": "Circuit breakers stay closed",
        "sli": "circuit_breaker_state{state='closed'} / (circuit_breaker_state{state='closed'} + circuit_breaker_state{state='open'})",
        "target": 0.99,
        "window": "30d",
    },
}

def get_slo_config() -> dict:
    """Get SLO configuration for Grafana/Alertmanager."""
    return SLO_DEFINITIONS
```

---

### Task 4.8: SLO Burn Rate Alerting

**Objective:** Implement multi-window burn rate alerting for SLOs.

**Files:**
- Create: `docker/monitoring/prometheus/rules/slo-burn-rate.yml`

```yaml
groups:
- name: slo-burn-rate
  rules:
  # Agent availability burn rate
  - alert: AgentAvailabilityBurnRate
    expr: |
      (
        (1 - sum(rate(agent_runs_total{success="true"}[1h])) / sum(rate(agent_runs_total[1h])))
        /
        (1 - 0.999)
      ) > 2
    for: 5m
    labels:
      severity: critical
      slo: agent_availability
    annotations:
      summary: "Agent availability burn rate 2x budget"

  # Fast burn rate (1h window, 2% budget)
  - alert: AgentAvailabilityFastBurn
    expr: |
      (
        (1 - sum(rate(agent_runs_total{success="true"}[5m])) / sum(rate(agent_runs_total[5m])))
        /
        (1 - 0.999)
      ) > 10
    for: 2m
    labels:
      severity: critical
      slo: agent_availability
    annotations:
      summary: "Agent availability fast burn rate 10x budget"
```

---

## Phase 4D: Distributed Tracing Visualization

### Task 4.9: Tempo TraceQL Queries for Common Debugging

**Objective:** Document and create saved queries for common debugging scenarios.

**Files:**
- Create: `docs/tracing/queries.md`

```markdown
# Common Tempo TraceQL Queries

## Find slow agent runs
```traceql
{ span.kind = "internal" && name =~ "agent\\..*\\.run" && duration > 10s }
```

## Find failed delegations
```traceql
{ span.kind = "internal" && name =~ "agent\\..*\\.delegate" && attributes["agent.success"] = false }
```

## Find governance blocks
```traceql
{ events.name = "governance.blocked" }
```

## Find circuit breaker opens
```traceql
{ attributes["circuit_breaker.state"] = "open" }
```

## Trace by tenant
```traceql
{ resource.attributes["tenant.id"] = "tenant-123" }
```

## Trace by correlation ID
```traceql
{ trace_id = "abc123" }
```
```

---

## Phase 4E: Logging Correlation

### Task 4.10: Add Trace ID to Structured Logs

**Objective:** Correlate logs with traces using trace_id/span_id.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`, `services/agent_orchestrator/main.py`

```python
# In agent.py run():
import opentelemetry.trace as trace

# Get current span context
span = trace.get_current_span()
span_context = span.get_span_context()
trace_id = format(span_context.trace_id, '032x')
span_id = format(span_context.span_id, '016x')

# Add to log context
logger.info("Agent run started", extra={
    "trace_id": trace_id,
    "span_id": span_id,
    "agent_id": str(self.agent_id),
    "agent_type": self.agent_type.value,
})
```

---

## Verification Checklist

- [ ] Task 4.1: Semantic conventions on agent spans
- [ ] Task 4.2: Span events for governance/approvals
- [ ] Task 4.3: Agent Performance dashboard
- [ ] Task 4.4: Circuit Breaker dashboard
- [ ] Task 4.5: DLQ dashboard
- [ ] Task 4.6: Cost Tracking dashboard
- [ ] Task 4.7: SLO definitions in code
- [ ] Task 4.8: SLO burn rate alerting rules
- [ ] Task 4.9: Tempo TraceQL queries documentation
- [ ] Task 4.10: Trace ID in structured logs
- [ ] All dashboards provisioned via `dashboards.yml`
- [ ] Dashboards visible in Grafana
- [ ] SLO burn rate alerts firing correctly in test
- [ ] TraceQL queries work in Tempo

---

## Execution Order

1. **Task 4.1** → Semantic conventions
2. **Task 4.2** → Span events
3. **Task 4.10** → Trace ID in logs
4. **Task 4.3** → Agent Performance dashboard
5. **Task 4.4** → Circuit Breaker dashboard
6. **Task 4.5** → DLQ dashboard
7. **Task 4.6** → Cost Tracking dashboard
8. **Task 4.7** → SLO definitions
9. **Task 4.8** → SLO burn rate alerts
9. **Task 4.9** → TraceQL queries doc

---

**Next Action:** Begin **Task 4.1** — Add semantic conventions to agent spans in `agent.py`.
