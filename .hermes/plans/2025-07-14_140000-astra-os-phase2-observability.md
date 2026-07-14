# ASTRA OS — Phase 2: Structured Observability Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task = 2-5 min focused work. TDD enforced. Independent reviewer subagent after each task.

**Goal:** Add distributed tracing (OpenTelemetry) and Prometheus metrics to Agent Orchestrator for full observability of agent runs, tool calls, and delegations.

**Architecture:** Clean Architecture + DDD. Target: `services/agent_orchestrator/`

**Tech Stack:** Python 3.12, OpenTelemetry SDK, OTLP HTTP exporter, Prometheus Client, pytest

---

## Phase 2A: OpenTelemetry Tracing Infrastructure

### Task 2.1: Create Telemetry Module with OTLP Exporter

**Objective:** Initialize OpenTelemetry with OTLP HTTP exporter, resource attributes, and tracer provider.

**Files:**
- Create: `services/agent_orchestrator/telemetry.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_telemetry.py
import pytest
from unittest.mock import patch, MagicMock

from services.agent_orchestrator.telemetry import init_tracing, get_tracer, TRACER

def test_init_tracing_creates_tracer_provider():
    with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
        mock_provider = MagicMock()
        mock_trace.TracerProvider.return_value = mock_provider
        mock_trace.get_tracer.return_value = MagicMock()
        
        tracer = init_tracing("test-service", "http://otel:4318/v1/traces")
        
        assert tracer is not None
        mock_trace.TracerProvider.assert_called_once()
        mock_provider.add_span_processor.assert_called_once()

def test_init_tracing_without_endpoint_creates_noop():
    with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
        mock_trace.get_tracer.return_value = MagicMock()
        
        tracer = init_tracing("test-service", None)
        
        assert tracer is not None
        mock_trace.TracerProvider.assert_called_once()
        # No span processor added when no endpoint

def test_get_tracer_returns_same_instance():
    tracer1 = get_tracer()
    tracer2 = get_tracer()
    assert tracer1 is tracer2
```

**Step 2: Run test to verify failure**

**Step 3: Implement telemetry module**

```python
# services/agent_orchestrator/telemetry.py
"""
OpenTelemetry tracing setup for Agent Orchestrator.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

_TRACER = None
_TRACER_PROVIDER = None

def init_tracing(service_name: str, otlp_endpoint: str | None = None) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Service name for resource attributes
        otlp_endpoint: OTLP HTTP endpoint (e.g., http://otel-collector:4318/v1/traces)
                      If None, creates noop tracer (no export)
    
    Returns:
        Configured tracer instance
    """
    global _TRACER, _TRACER_PROVIDER
    
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    provider = TracerProvider(resource=resource)
    
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER = provider
    _TRACER = trace.get_tracer(__name__)
    
    return _TRACER

def get_tracer() -> trace.Tracer:
    """Get the configured tracer, initializing with defaults if needed."""
    global _TRACER
    if _TRACER is None:
        _TRACER = init_tracing("astra-agent-orchestrator")
    return _TRACER

def shutdown_tracing() -> None:
    """Shutdown tracer provider, flushing spans."""
    global _TRACER_PROVIDER
    if _TRACER_PROVIDER:
        _TRACER_PROVIDER.shutdown()
        _TRACER_PROVIDER = None
```

**Step 4: Run test to verify pass**

**Step 5: Wire into main.py** — call `init_tracing()` in `main()` with env var for endpoint

---

### Task 2.2: Instrument Agent.run() with Spans

**Objective:** Wrap `Agent.run()` with span capturing agent_id, agent_type, autonomy_level, duration, tokens, cost, success, error.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_agent_tracing.py
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
async def test_agent_run_creates_span_with_attributes(agent_config, mock_context):
    """Agent.run() should create span with agent attributes."""
    agent = Agent(agent_config, agent_config.tenant_id)
    
    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        # Mock execute to return success
        agent.execute = AsyncMock(return_value=AgentResult(
            agent_id=agent_config.agent_id,
            success=True,
            duration_ms=150,
            tokens_used=100,
            cost_usd=0.001,
            iterations=1,
        ))
        
        result = await agent.run(mock_context, {"task": "test"})
        
        # Verify span created with correct name and attributes
        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args[0][0] == "agent.CEO.run"
        
        # Verify span attributes set
        mock_span.set_attribute.assert_any_call("agent.id", str(agent_config.agent_id))
        mock_span.set_attribute.assert_any_call("agent.type", "CEO")
        mock_span.set_attribute.assert_any_call("agent.autonomy_level", 1)
        mock_span.set_attribute.assert_any_call("agent.success", True)
        mock_span.set_attribute.assert_any_call("agent.duration_ms", 150)
        mock_span.set_attribute.assert_any_call("agent.tokens_used", 100)
        mock_span.set_attribute.assert_any_call("agent.cost_usd", 0.001)
        mock_span.set_attribute.assert_any_call("agent.iterations", 1)

@pytest.mark.asyncio
async def test_agent_run_records_exception_on_failure(agent_config, mock_context):
    """Failed agent run should record exception on span."""
    agent = Agent(agent_config, agent_config.tenant_id)
    
    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        agent.execute = AsyncMock(side_effect=RuntimeError("Agent failed"))
        
        with pytest.raises(RuntimeError):
            await agent.run(mock_context, {"task": "test"})
        
        mock_span.record_exception.assert_called_once()
        mock_span.set_attribute.assert_any_call("agent.success", False)
```

**Step 2: Run test to verify failure**

**Step 3: Modify Agent.run() in agent.py**

```python
# In agent.py, add import:
from services.agent_orchestrator.telemetry import get_tracer

TRACER = get_tracer()

# Modify run() method:
async def run(self, context: AgentContext, input_data: Any) -> AgentResult:
    """Run the agent with the given input."""
    await self.initialize(context)
    self._start_time = time.time()
    self._iteration = 0
    self._tool_calls = []
    self._tool_results = []
    self._sub_agent_results = []
    
    with TRACER.start_as_current_span(
        f"agent.{self.agent_type.value}.run",
        attributes={
            "agent.id": str(self.agent_id),
            "agent.type": self.agent_type.value,
            "agent.autonomy_level": self.config.autonomy_level,
        }
    ) as span:
        try:
            self.state = AgentState.RUNNING
            result = await self.execute(context, input_data)
            self.state = AgentState.COMPLETED
            
            # Record success attributes
            span.set_attribute("agent.success", result.success)
            span.set_attribute("agent.duration_ms", result.duration_ms)
            span.set_attribute("agent.tokens_used", result.tokens_used)
            span.set_attribute("agent.cost_usd", result.cost_usd)
            span.set_attribute("agent.iterations", result.iterations)
            if result.error:
                span.set_attribute("agent.error", result.error)
            
            return result
        except Exception as e:
            self.state = AgentState.FAILED
            span.record_exception(e)
            span.set_attribute("agent.success", False)
            span.set_attribute("agent.error", str(e))
            logger.exception("Agent %s failed: %s", self.agent_id, e)
            return AgentResult(
                agent_id=self.agent_id,
                success=False,
                error=str(e),
                duration_ms=int((time.time() - self._start_time) * 1000),
                iterations=self._iteration,
            )
        finally:
            self._record_metrics()
```

**Step 4: Run test to verify pass**

---

### Task 2.3: Instrument Agent.call_tool() with Spans

**Objective:** Wrap tool calls with span capturing tool_name, parameters, duration, success, error.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

**Step 1: Write failing test**

```python
# In test_agent_tracing.py
@pytest.mark.asyncio
async def test_call_tool_creates_span(agent_config, mock_context):
    """call_tool() should create span with tool attributes."""
    agent = Agent(agent_config, agent_config.tenant_id)
    
    with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        # Mock tool registry
        agent.tool_registry.execute_tool = AsyncMock(return_value={
            "success": True,
            "result": "tool output",
        })
        
        result = await agent.call_tool("test_tool", {"param": "value"}, mock_context)
        
        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args[0][0] == "agent.CEO.call_tool"
        
        mock_span.set_attribute.assert_any_call("tool.name", "test_tool")
        mock_span.set_attribute.assert_any_call("tool.success", True)
        mock_span.set_attribute.assert_any_call("tool.duration_ms", pytest.anything())
```

**Step 2: Modify call_tool() in agent.py**

```python
async def call_tool(
    self,
    tool_name: str,
    parameters: dict[str, Any],
    context: AgentContext | None = None,
) -> ToolResult:
    """Execute a tool through the registry, with governance enforcement."""
    self.state = AgentState.WAITING_FOR_TOOL
    
    with TRACER.start_as_current_span(
        f"agent.{self.agent_type.value}.call_tool",
        attributes={
            "agent.id": str(self.agent_id),
            "tool.name": tool_name,
        }
    ) as span:
        # ... existing governance logic ...
        
        call = ToolCall(tool_name=tool_name, parameters=parameters)
        self._tool_calls.append(call)
        
        start = time.time()
        try:
            result_data = await self.tool_registry.execute_tool(
                tool_name, parameters, context
            )
            duration_ms = int((time.time() - start) * 1000)
            
            result = ToolResult(
                call_id=call.call_id,
                tool_name=tool_name,
                success=result_data.get("success", False),
                result=result_data.get("result"),
                error=result_data.get("error"),
                duration_ms=duration_ms,
            )
            
            span.set_attribute("tool.success", result.success)
            span.set_attribute("tool.duration_ms", duration_ms)
            if result.error:
                span.set_attribute("tool.error", result.error)
            
            self._tool_results.append(result)
            self.state = AgentState.RUNNING
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("tool.success", False)
            span.set_attribute("tool.error", str(e))
            raise
```

---

### Task 2.4: Instrument Agent.delegate_to_subagent() with Spans

**Objective:** Wrap subagent delegation with span capturing subagent_type, parent/child relationship.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

```python
async def delegate_to_subagent(
    self,
    subagent_type: AgentType,
    input_data: Any,
    context: AgentContext | None = None,
) -> AgentResult:
    """Delegate a task to a sub-agent."""
    self.state = AgentState.WAITING_FOR_SUBAGENT
    
    with TRACER.start_as_current_span(
        f"agent.{self.agent_type.value}.delegate",
        attributes={
            "agent.id": str(self.agent_id),
            "subagent.type": subagent_type.value,
        }
    ) as span:
        registry = get_agent_registry()
        subagent = registry.create_agent(subagent_type, self.tenant_id)
        
        sub_context = context.child_context(subagent.agent_id) if context else context
        span.set_attribute("subagent.id", str(subagent.agent_id))
        
        result = await subagent.run(sub_context, input_data)
        
        span.set_attribute("subagent.success", result.success)
        span.set_attribute("subagent.duration_ms", result.duration_ms)
        
        self._sub_agent_results.append(result)
        return result
```

---

## Phase 2B: Prometheus Metrics

### Task 2.5: Create Metrics Module

**Objective:** Define Prometheus counters, histograms, gauges for agent performance.

**Files:**
- Create: `services/agent_orchestrator/metrics.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_metrics.py
import pytest
from prometheus_client import CollectorRegistry

from services.agent_orchestrator.metrics import (
    AGENT_RUNS,
    AGENT_DURATION,
    AGENT_TOKENS,
    AGENT_COST,
    AGENT_ACTIVE,
    AGENT_TOOL_CALLS,
    AGENT_DELEGATIONS,
    record_agent_run,
    record_tool_call,
    record_delegation,
    AgentMetricsContext,
)

def test_metrics_defined():
    """All metric instruments should be defined."""
    assert AGENT_RUNS is not None
    assert AGENT_DURATION is not None
    assert AGENT_TOKENS is not None
    assert AGENT_COST is not None
    assert AGENT_ACTIVE is not None
    assert AGENT_TOOL_CALLS is not None
    assert AGENT_DELEGATIONS is not None

def test_record_agent_run_increments_counters():
    """record_agent_run should increment all agent run metrics."""
    registry = CollectorRegistry()
    # Use custom registry to isolate test
    from prometheus_client.core import CollectorRegistry
    from prometheus_client import Counter, Histogram
    
    # Direct test of metric functions
    record_agent_run("CEO", True, 1.5, 100, 0.001)
    
    # Verify counters incremented (check via samples)
    samples = list(AGENT_RUNS.collect())
    assert len(samples) > 0

def test_agent_metrics_context_manager():
    """AgentMetricsContext should increment/decrement active gauge."""
    with AgentMetricsContext("CEO"):
        pass  # Should increment on enter, decrement on exit
```

**Step 2: Implement metrics module**

```python
# services/agent_orchestrator/metrics.py
"""
Prometheus metrics for Agent Orchestrator.
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from contextlib import contextmanager

# Agent run metrics
AGENT_RUNS = Counter(
    "agent_runs_total",
    "Total agent runs",
    ["agent_type", "success"]
)

AGENT_DURATION = Histogram(
    "agent_duration_seconds",
    "Agent run duration in seconds",
    ["agent_type"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
)

AGENT_TOKENS = Counter(
    "agent_tokens_total",
    "Total tokens consumed by agents",
    ["agent_type"]
)

AGENT_COST = Counter(
    "agent_cost_usd_total",
    "Total cost in USD for agent runs",
    ["agent_type"]
)

AGENT_ACTIVE = Gauge(
    "agent_active_count",
    "Currently running agents",
    ["agent_type"]
)

# Tool call metrics
AGENT_TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "Total tool calls by agents",
    ["agent_type", "tool_name", "success"]
)

AGENT_TOOL_DURATION = Histogram(
    "agent_tool_duration_seconds",
    "Tool call duration in seconds",
    ["agent_type", "tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

# Delegation metrics
AGENT_DELEGATIONS = Counter(
    "agent_delegations_total",
    "Total subagent delegations",
    ["agent_type", "subagent_type", "success"]
)

def record_agent_run(
    agent_type: str,
    success: bool,
    duration_seconds: float,
    tokens: int,
    cost_usd: float,
) -> None:
    """Record metrics for a completed agent run."""
    AGENT_RUNS.labels(agent_type=agent_type, success=str(success).lower()).inc()
    AGENT_DURATION.labels(agent_type=agent_type).observe(duration_seconds)
    AGENT_TOKENS.labels(agent_type=agent_type).inc(tokens)
    AGENT_COST.labels(agent_type=agent_type).inc(cost_usd)

def record_tool_call(
    agent_type: str,
    tool_name: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """Record metrics for a tool call."""
    AGENT_TOOL_CALLS.labels(
        agent_type=agent_type,
        tool_name=tool_name,
        success=str(success).lower()
    ).inc()
    AGENT_TOOL_DURATION.labels(
        agent_type=agent_type,
        tool_name=tool_name
    ).observe(duration_seconds)

def record_delegation(
    agent_type: str,
    subagent_type: str,
    success: bool,
) -> None:
    """Record metrics for a subagent delegation."""
    AGENT_DELEGATIONS.labels(
        agent_type=agent_type,
        subagent_type=subagent_type,
        success=str(success).lower()
    ).inc()

class AgentMetricsContext:
    """Context manager for tracking active agent count."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
    
    def __enter__(self):
        AGENT_ACTIVE.labels(agent_type=self.agent_type).inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        AGENT_ACTIVE.labels(agent_type=self.agent_type).dec()
        return False

@contextmanager
def track_agent_run(agent_type: str):
    """Context manager that tracks agent run metrics automatically."""
    start = time.time()
    success = False
    tokens = 0
    cost = 0.0
    
    class RunTracker:
        def __init__(self):
            self.tokens = 0
            self.cost = 0.0
            self.success = False
        
        def set_success(self, success: bool, tokens: int = 0, cost: float = 0.0):
            self.success = success
            self.tokens = tokens
            self.cost = cost
    
    tracker = RunTracker()
    AGENT_ACTIVE.labels(agent_type=agent_type).inc()
    
    try:
        yield tracker
        tracker.set_success(True)
    except Exception:
        tracker.set_success(False)
        raise
    finally:
        duration = time.time() - start
        AGENT_ACTIVE.labels(agent_type=agent_type).dec()
        record_agent_run(
            agent_type=agent_type,
            success=tracker.success,
            duration_seconds=duration,
            tokens=tracker.tokens,
            cost_usd=tracker.cost,
        )
```

---

### Task 2.6: Wire Metrics into Agent.run() and call_tool()

**Files:**
- Modify: `services/agent_orchestrator/agent.py`

```python
# Add imports
from services.agent_orchestrator.metrics import (
    record_agent_run,
    record_tool_call,
    record_delegation,
    AgentMetricsContext,
)

# In Agent.run(), wrap with metrics context:
async def run(self, context: AgentContext, input_data: Any) -> AgentResult:
    with AgentMetricsContext(self.agent_type.value):
        with TRACER.start_as_current_span(...) as span:
            # ... existing implementation ...
            # At end of successful run:
            record_agent_run(
                agent_type=self.agent_type.value,
                success=result.success,
                duration_seconds=result.duration_ms / 1000,
                tokens=result.tokens_used,
                cost_usd=result.cost_usd,
            )
            return result

# In call_tool():
async def call_tool(self, tool_name: str, parameters: dict, context: AgentContext | None = None):
    start = time.time()
    try:
        # ... existing implementation ...
        record_tool_call(
            agent_type=self.agent_type.value,
            tool_name=tool_name,
            success=result.success,
            duration_seconds=(time.time() - start),
        )
        return result
    except Exception as e:
        record_tool_call(
            agent_type=self.agent_type.value,
            tool_name=tool_name,
            success=False,
            duration_seconds=(time.time() - start),
        )
        raise

# In delegate_to_subagent():
async def delegate_to_subagent(self, subagent_type: AgentType, input_data: Any, context: AgentContext | None = None):
    # ... existing implementation ...
    record_delegation(
        agent_type=self.agent_type.value,
        subagent_type=subagent_type.value,
        success=result.success,
    )
```

---

### Task 2.7: Expose /metrics Endpoint on Health Server

**Files:**
- Modify: `services/agent_orchestrator/main.py`

```python
# In _start_health_server():
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

async def metrics_endpoint(request):
    """Prometheus metrics endpoint."""
    return web.Response(
        body=generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )

app.router.add_get("/metrics", metrics_endpoint)
```

---

## Verification Checklist

- [ ] Task 2.1: Telemetry module with OTLP exporter
- [ ] Task 2.2: Agent.run() spans with attributes
- [ ] Task 2.3: call_tool() spans
- [ ] Task 2.4: delegate_to_subagent() spans
- [ ] Task 2.5: Prometheus metrics module
- [ ] Task 2.6: Metrics wired into agent methods
- [ ] Task 2.7: /metrics endpoint exposed
- [ ] All tests pass: `pytest services/agent_orchestrator/tests/ -q`
- [ ] Spans visible in Tempo/Grafana
- [ ] Metrics scraped by Prometheus, dashboards update

---

## Execution Order

1. **Task 2.1** → Telemetry infrastructure
2. **Task 2.2** → Agent.run() spans
3. **Task 2.3** → call_tool() spans
4. **Task 2.4** → delegate_to_subagent() spans
5. **Task 2.5** → Prometheus metrics module
6. **Task 2.6** → Wire metrics into agent
7. **Task 2.7** → Expose /metrics endpoint

---

**Next Action:** Begin **Task 2.1** — Create `services/agent_orchestrator/telemetry.py` with TDD.