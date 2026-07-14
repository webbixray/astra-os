# ASTRA OS — Phase 3: Resilience Patterns Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task = 2-5 min focused work. TDD enforced. Independent reviewer subagent after each task.

**Goal:** Add circuit breaker on Model Router, Redis Streams DLQ for failed async tasks, and dead letter alerting.

**Architecture:** Clean Architecture + DDD. Target: `services/agent_orchestrator/`

**Tech Stack:** Python 3.12, Redis 7 Streams, asyncio, pytest

---

## Phase 3A: Circuit Breaker on Model Router

### Task 3.1: Create Circuit Breaker Module

**Objective:** Generic circuit breaker implementation with states (CLOSED, OPEN, HALF_OPEN), configurable thresholds, and metrics.

**Files:**
- Create: `services/agent_orchestrator/resilience.py`

**Step 1: Write failing test**

```python
# services/agent_orchestrator/tests/test_circuit_breaker.py
import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from services.agent_orchestrator.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitOpenError,
)

@pytest.fixture
def config():
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=1.0,
    )

@pytest.mark.asyncio
async def test_circuit_closed_allows_calls(config):
    """CLOSED circuit allows calls through."""
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(return_value="success")
    
    result = await cb.call(mock_func)
    
    assert result == "success"
    assert mock_func.call_count == 1
    assert cb.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_opens_after_failure_threshold(config):
    """Circuit opens after failure_threshold failures."""
    config.failure_threshold = 2
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(side_effect=RuntimeError("fail"))
    
    # First failure
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1
    
    # Second failure -> opens
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2

@pytest.mark.asyncio
async def test_circuit_open_rejects_calls(config):
    """OPEN circuit rejects calls immediately with CircuitOpenError."""
    config.failure_threshold = 1
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(side_effect=RuntimeError("fail"))
    
    # Trigger open
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    
    # Next call should be rejected
    with pytest.raises(CircuitOpenError):
        await cb.call(mock_func)

@pytest.mark.asyncio
async def test_half_open_after_timeout(config):
    """After timeout, circuit enters HALF_OPEN for probe."""
    config.failure_threshold = 1
    config.timeout_seconds = 0.1
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(side_effect=RuntimeError("fail"))
    
    # Trigger open
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(0.15)
    
    # Next call should be allowed (HALF_OPEN)
    mock_func.side_effect = None
    mock_func.return_value = "success"
    result = await cb.call(mock_func)
    
    assert result == "success"
    assert cb.state == CircuitState.HALF_OPEN

@pytest.mark.asyncio
async def test_half_open_success_closes_circuit(config):
    """Success threshold in HALF_OPEN closes circuit."""
    config.failure_threshold = 1
    config.success_threshold = 2
    config.timeout_seconds = 0.1
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(side_effect=RuntimeError("fail"))
    
    # Open circuit
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    await asyncio.sleep(0.15)
    
    # First success
    mock_func.side_effect = None
    mock_func.return_value = "success"
    await cb.call(mock_func)
    assert cb.state == CircuitState.HALF_OPEN
    
    # Second success -> CLOSED
    await cb.call(mock_func)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

@pytest.mark.asyncio
async def test_half_open_failure_reopens_circuit(config):
    """Failure in HALF_OPEN immediately reopens circuit."""
    config.failure_threshold = 1
    config.timeout_seconds = 0.1
    cb = CircuitBreaker("test", config)
    mock_func = AsyncMock(side_effect=RuntimeError("fail"))
    
    # Open circuit
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    await asyncio.sleep(0.15)
    
    # Failure in HALF_OPEN
    with pytest.raises(RuntimeError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_concurrent_calls_thread_safe(config):
    """Circuit breaker should be thread-safe for concurrent calls."""
    config.failure_threshold = 10  # High threshold
    cb = CircuitBreaker("test", config)
    
    async def slow_fail():
        await asyncio.sleep(0.01)
        raise RuntimeError("fail")
    
    # Fire 20 concurrent calls
    results = await asyncio.gather(
        *[cb.call(slow_fail) for _ in range(20)],
        return_exceptions=True
    )
    
    # All should be RuntimeError (not CircuitOpenError mid-flight)
    errors = [r for r in results if isinstance(r, RuntimeError)]
    assert len(errors) == 20