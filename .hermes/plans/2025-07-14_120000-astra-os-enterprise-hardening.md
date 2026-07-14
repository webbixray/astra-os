# ASTRA OS — Enterprise Hardening Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task = 2-5 min focused work. TDD enforced. Independent reviewer subagent after each task.

**Goal:** Take Astra OS from 8.8/10 (production-ready) to 9.8/10 (industry-defining) by adding process-level supervision, structured observability, resilience patterns, and DLQ to the Agent Orchestrator.

**Architecture:** Clean Architecture + DDD + Event-Driven. Target: Agent Orchestrator service (`services/agent_orchestrator/`)

**Tech Stack:** Python 3.12, FastAPI, asyncpg, Redis 7, asyncio, OpenTelemetry, Prometheus, pytest

---

## Phase 1: Process-Level Supervision (CRITICAL — Blocks Scale/Reliability)

### Task 1.1: Create Supervisor Module with Bounded Restart Logic

**Objective:** Implement in-process supervisor wrapping `AgentOrchestrator.run()` with exponential backoff, crash-loop guard, and escape hatches.

**Files:**
- Create: `services/agent_orchestrator/supervisor.py`
- Modify: `services/agent_orchestrator/main.py` (wire supervisor)

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_supervisor.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from services.agent_orchestrator.supervisor import Supervisor, SupervisorConfig, ExitReason

@pytest.fixture
def config():
    return SupervisorConfig(
        max_restarts=3,
        restart_window_seconds=60,
        base_backoff_seconds=1,
        max_backoff_seconds=15,
        backoff_multiplier=2.0,
    )

@pytest.mark.asyncio
async def test_clean_exit_does_not_restart(config):
    """SystemExit(0) or KeyboardInterrupt should stop supervisor without restart."""
    supervisor = Supervisor(config)
    mock_run = AsyncMock(side_effect=SystemExit(0))
    
    await supervisor.run(mock_run)
    
    assert mock_run.call_count == 1
    assert supervisor.restart_count == 0

@pytest.mark.asyncio
async def test_nonzero_systemexit_does_not_restart(config):
    """SystemExit(non-zero) = deterministic failure, no restart."""
    supervisor = Supervisor(config)
    mock_run = AsyncMock(side_effect=SystemExit(1))
    
    with pytest.raises(SystemExit) as exc:
        await supervisor.run(mock_run)
    
    assert exc.value.code == 1
    assert mock_run.call_count == 1

@pytest.mark.asyncio
async def test_unhandled_exception_triggers_restart_with_backoff(config):
    """Any other exception triggers restart with exponential backoff."""
    supervisor = Supervisor(config)
    call_count = 0
    
    async def flaky_run():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("transient failure")
        return "success"
    
    result = await supervisor.run(flaky_run)
    
    assert result == "success"
    assert call_count == 3
    assert supervisor.restart_count == 2

@pytest.mark.asyncio
async def test_crash_loop_guard_exits_after_max_restarts(config):
    """More than max_restarts within window -> exit 1."""
    config.max_restarts = 2
    config.restart_window_seconds = 300
    supervisor = Supervisor(config)
    
    async def always_fails():
        raise RuntimeError("permanent failure")
    
    with pytest.raises(SystemExit) as exc:
        await supervisor.run(always_fails)
    
    assert exc.value.code == 1
    assert supervisor.restart_count == 2

@pytest.mark.asyncio
async def test_no_supervise_env_var_disables_supervisor(config):
    """HERMES_ORCHESTRATOR_NO_SUPERVISE=1 disables supervisor entirely."""
    import os
    os.environ["HERMES_ORCHESTRATOR_NO_SUPERVISE"] = "1"
    try:
        config = SupervisorConfig()
        supervisor = Supervisor(config)
        mock_run = AsyncMock(return_value="done")
        
        result = await supervisor.run(mock_run)
        
        assert result == "done"
        assert mock_run.call_count == 1
    finally:
        del os.environ["HERMES_ORCHESTRATOR_NO_SUPERVISE"]
```

**Step 2: Run test to verify failure** → `pytest services/agent_orchestrator/tests/test_supervisor.py -v`

**Step 3: Implement minimal supervisor**

```python
# services/agent_orchestrator/supervisor.py
import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

class ExitReason(Enum):
    CLEAN = "clean"
    DETERMINISTIC_FAILURE = "deterministic_failure"
    CRASH_LOOP = "crash_loop"
    DISABLED = "disabled"

@dataclass
class SupervisorConfig:
    max_restarts: int = 10
    restart_window_seconds: int = 600
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    disable_env_var: str = "HERMES_ORCHESTRATOR_NO_SUPERVISE"

@dataclass
class Supervisor:
    config: SupervisorConfig
    restart_count: int = 0
    restart_timestamps: list[float] = field(default_factory=list)
    _backoff: float = 1.0
    
    def __post_init__(self):
        if os.getenv(self.config.disable_env_var) == "1":
            self._disabled = True
        else:
            self._disabled = False
        self._backoff = self.config.base_backoff_seconds
    
    async def run(self, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        if self._disabled:
            return await coro_factory()
        
        while True:
            try:
                return await coro_factory()
            except SystemExit as e:
                if e.code == 0:
                    return None
                raise
            except KeyboardInterrupt:
                raise
            except BaseException:
                raise
            except Exception as e:
                await self._handle_crash(e)
    
    async def _handle_crash(self, error: Exception) -> None:
        now = time.monotonic()
        self.restart_timestamps = [t for t in self.restart_timestamps if now - t < self.config.restart_window_seconds]
        self.restart_timestamps.append(now)
        self.restart_count += 1
        
        if len(self.restart_timestamps) > self.config.max_restarts:
            raise SystemExit(1)
        
        # Sleep in small slices for signal responsiveness
        remaining = self._backoff
        while remaining > 0:
            slice_ms = min(0.25, remaining)
            await asyncio.sleep(slice_ms)
            remaining -= slice_ms
        
        self._backoff = min(self._backoff * self.config.backoff_multiplier, self.config.max_backoff_seconds)
```

**Step 4: Run test to verify pass** → `pytest services/agent_orchestrator/tests/test_supervisor.py -v`

**Step 5: Wire into main.py**

```python
# services/agent_orchestrator/main.py — modify main()
from services.agent_orchestrator.supervisor import Supervisor, SupervisorConfig

async def main() -> None:
    logging.basicConfig(...)
    settings = Settings()
    orchestrator = AgentOrchestrator(settings)
    
    supervisor = Supervisor(SupervisorConfig())
    
    async def run_orchestrator():
        await orchestrator.run()
    
    try:
        await supervisor.run(run_orchestrator)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Supervisor exited with code %d", e.code)
            sys.exit(e.code)
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)
```

**Step 6: Run full test suite** → `pytest services/agent_orchestrator/tests/ -q`

**Step 7: Commit** → `git add -A && git commit -m "feat(orchestrator): add bounded in-process supervisor with crash-loop guard"`

---

### Task 1.2: Add Liveness Endpoint `/api/health/live`

**Objective:** Cheap, unauthenticated liveness probe for K8s `livenessProbe` — returns `{ok: true, uptime_seconds: float, version: str}` using monotonic clock.

**Files:**
- Modify: `services/agent_orchestrator/main.py` (add HTTP server)
- Create: `services/agent_orchestrator/health.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_health.py
import pytest
from httpx import AsyncClient
import time

@pytest.mark.asyncio
async def test_liveness_endpoint_returns_ok():
    from services.agent_orchestrator.health import create_health_app
    from services.agent_orchestrator.supervisor import Supervisor, SupervisorConfig
    
    app = create_health_app(Supervisor(SupervisorConfig()))
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], float)
    assert data["uptime_seconds"] >= 0
    assert "version" in data

@pytest.mark.asyncio
async def test_liveness_endpoint_works_without_auth():
    """No Authorization header required."""
    from services.agent_orchestrator.health import create_health_app
    from services.agent_orchestrator.supervisor import Supervisor, SupervisorConfig
    
    app = create_health_app(Supervisor(SupervisorConfig()))
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health/live")
    
    assert response.status_code == 200
    assert response.json()["ok"] is True
```

**Step 2: Run test to verify failure**

**Step 3: Implement health module**

```python
# services/agent_orchestrator/health.py
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

from services.agent_orchestrator.supervisor import Supervisor

_START_MONOTONIC = time.monotonic()
_VERSION = "0.1.0"

class HealthResponse(BaseModel):
    ok: bool
    uptime_seconds: float
    version: str

@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield

def create_health_app(supervisor: Supervisor) -> FastAPI:
    app = FastAPI(title="Agent Orchestrator Health", lifespan=_lifespan)
    
    @app.get("/api/health/live", response_model=HealthResponse)
    async def liveness():
        return HealthResponse(
            ok=True,
            uptime_seconds=time.monotonic() - _START_MONOTONIC,
            version=_VERSION,
        )
    
    return app
```

**Step 4: Run test to verify pass**

**Step 5: Wire into main.py — run health server on separate port (8081)**

```python
# In main.py, add to AgentOrchestrator.__init__
self.health_server = None
self.health_port = 8081

# In initialize(), after Redis connected:
from services.agent_orchestrator.health import create_health_app
import uvicorn

health_app = create_health_app(self)
config = uvicorn.Config(health_app, host="0.0.0.0", port=self.health_port, log_level="warning")
self.health_server = uvicorn.Server(config)
asyncio.create_task(self.health_server.serve())

# In shutdown():
if self.health_server:
    await self.health_server.shutdown()
```

**Step 6: Run full test suite**

**Step 7: Commit**

---

### Task 1.3: K8s Liveness/Readiness Probes in Deployment

**Files:** `k8s/worker-deployment.yaml`

```yaml
# Add to worker-deployment.yaml containers[0]
livenessProbe:
  httpGet:
    path: /api/health/live
    port: 8081
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 8081
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**Note:** `/api/health/ready` will be added in Phase 2 (checks DB/Redis connectivity).

---

## Phase 2: Structured Observability (HIGH — Enables Debugging at Scale)

### Task 2.1: OpenTelemetry Spans on Agent Lifecycle

**Objective:** Wrap `Agent.run()`, `Agent.call_tool()`, `Agent.delegate_to_subagent()` with spans exporting `agent.id`, `agent.type`, `duration_ms`, `tokens`, `cost_usd`, `success`, `iterations`.

**Files:**
- Modify: `services/agent_orchestrator/agent.py`
- Create: `services/agent_orchestrator/telemetry.py`

**Step 1: Write failing test** — Verify span attributes emitted

**Step 2: Implement telemetry module with OTLP exporter**

```python
# services/agent_orchestrator/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def init_tracing(service_name: str, otlp_endpoint: str | None = None):
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)

TRACER = trace.get_tracer(__name__)
```

**Step 3: Instrument Agent.run()**

```python
# In agent.py, modify run():
async def run(self, context: AgentContext, input_data: Any) -> AgentResult:
    with TRACER.start_as_current_span(
        f"agent.{self.agent_type.value}.run",
        attributes={
            "agent.id": str(self.agent_id),
            "agent.type": self.agent_type.value,
            "agent.autonomy_level": self.config.autonomy_level,
        }
    ) as span:
        try:
            result = await self.execute(context, input_data)
            span.set_attribute("agent.success", result.success)
            span.set_attribute("agent.duration_ms", result.duration_ms)
            span.set_attribute("agent.tokens_used", result.tokens_used)
            span.set_attribute("agent.cost_usd", result.cost_usd)
            span.set_attribute("agent.iterations", result.iterations)
            if result.error:
                span.set_attribute("agent.error", result.error)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("agent.success", False)
            raise
```

**Step 4: Run tests, commit**

---

### Task 2.2: Prometheus Metrics for Agent Performance

**Objective:** Export `agent_runs_total{type,success}`, `agent_duration_seconds_bucket{type}`, `agent_tokens_total{type}`, `agent_cost_usd_total{type}`, `agent_active_count{type}`.

**Files:**
- Create: `services/agent_orchestrator/metrics.py`
- Modify: `services/agent_orchestrator/main.py` (expose `/metrics`)

**Step 1: Write failing test** — Verify metrics increment

**Step 2: Implement metrics module**

```python
# services/agent_orchestrator/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

AGENT_RUNS = Counter(
    "agent_runs_total",
    "Total agent runs",
    ["agent_type", "success"]
)
AGENT_DURATION = Histogram(
    "agent_duration_seconds",
    "Agent run duration",
    ["agent_type"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
)
AGENT_TOKENS = Counter(
    "agent_tokens_total",
    "Total tokens consumed",
    ["agent_type"]
)
AGENT_COST = Counter(
    "agent_cost_usd_total",
    "Total cost in USD",
    ["agent_type"]
)
AGENT_ACTIVE = Gauge(
    "agent_active_count",
    "Currently running agents",
    ["agent_type"]
)

def record_agent_run(agent_type: str, success: bool, duration: float, tokens: int, cost: float):
    AGENT_RUNS.labels(agent_type=agent_type, success=str(success).lower()).inc()
    AGENT_DURATION.labels(agent_type=agent_type).observe(duration)
    AGENT_TOKENS.labels(agent_type=agent_type).inc(tokens)
    AGENT_COST.labels(agent_type=agent_type).inc(cost)

class AgentMetricsContext:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.start = 0
    
    def __enter__(self):
        self.start = time.monotonic()
        AGENT_ACTIVE.labels(agent_type=self.agent_type).inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        AGENT_ACTIVE.labels(agent_type=self.agent_type).dec()
```

**Step 3: Wire into Agent.run() and expose `/metrics` on health port**

**Step 4: Run tests, commit**

---

### Task 2.3: Readiness Endpoint `/api/health/ready`

**Objective:** Checks DB pool + Redis connectivity before returning 200.

**Files:** `services/agent_orchestrator/health.py`

```python
@app.get("/api/health/ready")
async def readiness(request: Request):
    orchestrator: AgentOrchestrator = request.app.state.orchestrator
    checks = {}
    
    # DB check
    try:
        async with orchestrator.pg_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {e}"
    
    # Redis check
    try:
        await orchestrator.redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"failed: {e}"
    
    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        {"ready": all_ok, "checks": checks},
        status_code=200 if all_ok else 503
    )
```

---

## Phase 3: Resilience Patterns (HIGH — Prevents Cascading Failures)

### Task 3.1: Circuit Breaker on Model Router

**Objective:** Per-provider circuit breaker (NIM, OpenAI, Anthropic, Gemini) with half-open probe, metrics.

**Files:**
- Create: `services/agent_orchestrator/resilience.py`
- Modify: Model router (wherever provider calls happen)

**Implementation:** Use `pybreaker` or custom state machine:

```python
# services/agent_orchestrator/resilience.py
import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Awaitable

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0

@dataclass
class CircuitBreaker:
    name: str
    config: CircuitBreakerConfig
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.last_failure_time >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._on_success()
            return result
        except Exception as e:
            async with self._lock:
                self._on_failure()
            raise
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

class CircuitOpenError(Exception):
    pass
```

**Step 1: Write test** — Verify state transitions

**Step 2: Implement, wire into model router fallback chain**

**Step 3: Export metrics:** `circuit_breaker_state{name,state}`, `circuit_breaker_calls_total{name,result}`

---

### Task 3.2: Dead Letter Queue for Failed Agent Tasks

**Objective:** Failed async tasks (from Redis Streams consumer groups) go to DLQ after max retries, with alerting.

**Files:**
- Create: `services/agent_orchestrator/dlq.py`
- Modify: Worker consumer logic

```python
# services/agent_orchestrator/dlq.py
import json
import time
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class DeadLetter:
    original_stream: str
    message_id: str
    payload: dict[str, Any]
    error: str
    retry_count: int
    failed_at: float
    consumer_group: str

class DeadLetterQueue:
    def __init__(self, redis_client, dlq_stream: str = "astra:dlq"):
        self.redis = redis_client
        self.dlq_stream = dlq_stream
    
    async def add(self, dead_letter: DeadLetter) -> str:
        return await self.redis.xadd(
            self.dlq_stream,
            {"data": json.dumps(asdict(dead_letter))}
        )
    
    async def get_pending_count(self) -> int:
        info = await self.redis.xinfo_stream(self.dlq_stream)
        return info["length"]
```

**Wire into consumer:** After max retries (3), `await dlq.add(...)` and `await redis.xack(...)`, then alert if `dlq_pending > 100`.

---

## Phase 4: Developer Experience & Quality Gates (MEDIUM)

### Task 4.1: Pre-commit Hooks with Ruff + MyPy + Bandit

**Files:** `.pre-commit-config.yaml` (root)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, fastapi, sqlalchemy]
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: [-r, apps/api/app, -x, tests]
```

---

### Task 4.2: Contract Testing for Agent ↔ Tool Interface

**Files:** `services/agent_orchestrator/tests/contract/test_tool_registry.py`

```python
# Verify every registered tool matches its ToolDefinition schema
def test_all_tools_match_definition():
    from services.agent_orchestrator.tools import tool_registry
    for name, tool in tool_registry._tools.items():
        definition = tool.definition
        # Validate schema can be serialized
        import json
        json.dumps(definition.model_dump())
        # Validate required fields present
        assert definition.name == name
        assert definition.description
        for param in definition.parameters:
            assert param.name
            assert param.type in ("string", "integer", "number", "boolean", "object", "array")
```

---

## Phase 5: Documentation & Runbooks (MEDIUM)

### Task 5.1: Runbook for Agent Orchestrator Operations

**File:** `docs/runbooks/agent-orchestrator.md`

```markdown
# Agent Orchestrator Runbook

## Service Overview
- Port: 8001 (API), 8081 (Health/Metrics)
- Supervisor: In-process, bounded restarts (max 10/10min)
- DLQ: Redis stream `astra:dlq`

## Common Scenarios

### High Restart Rate
1. Check `/api/health/live` — if failing, pod will be restarted by K8s
2. Check logs: `kubectl logs -l app=astra-worker -c orchestrator`
3. Check metrics: `agent_runs_total{success="false"}` spike?
4. Check DLQ depth: `redis-cli XLEN astra:dlq`

### Circuit Breaker Open
1. Check `circuit_breaker_state{name="openai",state="open"}`
2. Verify provider API status
3. Manual reset: `redis-cli DEL circuit:openai:state`

### DLQ Alert
1. `redis-cli XRANGE astra:dlq - + COUNT 10`
2. Inspect payload, fix root cause
3. Replay: `redis-cli XREAD COUNT 1 STREAMS astra:dlq 0` → re-publish to original stream
```

---

## Verification Checklist (Definition of Done)

- [ ] All Phase 1 tests pass (supervisor, health endpoints)
- [ ] K8s liveness/readiness probes configured and tested
- [ ] Phase 2: OTel spans visible in Tempo/Grafana
- [ ] Phase 2: Prometheus metrics scraped, dashboards update
- [ ] Phase 3: Circuit breaker opens/closes correctly under load
- [ ] Phase 3: DLQ captures failed messages, alert fires at threshold
- [ ] Phase 4: Pre-commit hooks run on every commit
- [ ] Phase 4: Contract tests catch schema drift
- [ ] Phase 5: Runbook exists and is accurate
- [ ] Full test suite: `pytest services/agent_orchestrator/tests/ -q` → 0 failures
- [ ] CI pipeline green: `github/workflows/ci.yml` passes
- [ ] Docker image builds: `docker build -f apps/api/Dockerfile .`

---

## Execution Order

1. **Task 1.1** → Supervisor (blocks everything else)
2. **Task 1.2** → Liveness endpoint
3. **Task 1.3** → K8s probes
4. **Task 2.1** → OTel spans
5. **Task 2.2** → Prometheus metrics
6. **Task 2.3** → Readiness endpoint
7. **Task 3.1** → Circuit breaker
8. **Task 3.2** → DLQ
9. **Task 4.1** → Pre-commit
10. **Task 4.2** → Contract tests
11. **Task 5.1** → Runbook

---

**Next Action:** Begin **Task 1.1** — Create `services/agent_orchestrator/supervisor.py` with TDD.