"""Tests for circuit breaker resilience patterns."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from astra_agent_orchestrator.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    create_circuit_breaker,
    get_circuit_breaker_registry,
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    @pytest.fixture
    def config(self):
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
        )

    @pytest.mark.asyncio
    async def test_circuit_closed_allows_calls(self, config):
        """CLOSED circuit allows calls through."""
        cb = CircuitBreaker("test", config)
        mock_func = AsyncMock(return_value="success")

        result = await cb.call(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failure_threshold(self, config):
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
    async def test_circuit_open_rejects_calls(self, config):
        """OPEN circuit rejects calls immediately with CircuitOpenError."""
        config.failure_threshold = 1
        cb = CircuitBreaker("test", config)
        mock_func = AsyncMock(side_effect=RuntimeError("fail"))

        # Trigger open
        with pytest.raises(RuntimeError):
            await cb.call(mock_func)

        # Next call should be rejected
        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(mock_func)

        assert exc_info.value.name == "test"
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, config):
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
    async def test_half_open_success_closes_circuit(self, config):
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
    async def test_half_open_failure_reopens_circuit(self, config):
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
    async def test_concurrent_calls_thread_safe(self, config):
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

    @pytest.mark.asyncio
    async def test_exclude_exceptions_dont_count_as_failures(self, config):
        """Excluded exceptions should not count as failures."""
        config.failure_threshold = 2
        config.exclude_exceptions = (ValueError,)
        cb = CircuitBreaker("test", config)

        async def raise_value_error():
            raise ValueError("excluded")

        async def raise_runtime_error():
            raise RuntimeError("not excluded")

        # ValueError should not count
        with pytest.raises(ValueError):
            await cb.call(raise_value_error)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

        # RuntimeError should count
        with pytest.raises(RuntimeError):
            await cb.call(raise_runtime_error)
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_reset_closes_circuit(self, config):
        """reset() should close circuit and clear counts."""
        config.failure_threshold = 1
        cb = CircuitBreaker("test", config)
        mock_func = AsyncMock(side_effect=RuntimeError("fail"))

        # Open circuit
        with pytest.raises(RuntimeError):
            await cb.call(mock_func)
        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_force_open(self, config):
        """force_open() should immediately open circuit."""
        cb = CircuitBreaker("test", config)

        cb.force_open()
        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitOpenError):
            await cb.call(AsyncMock(return_value="success"))


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        registry = get_circuit_breaker_registry()
        registry._breakers.clear()

    def test_get_or_create_returns_new_breaker(self):
        """get_or_create should create new breaker for unknown name."""
        registry = get_circuit_breaker_registry()
        cb = registry.get_or_create("test")

        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED

    def test_get_or_create_returns_existing_breaker(self):
        """get_or_create should return existing breaker for known name."""
        registry = get_circuit_breaker_registry()
        cb1 = registry.get_or_create("test")
        cb2 = registry.get_or_create("test")

        assert cb1 is cb2

    def test_get_returns_none_for_unknown(self):
        """get() should return None for unknown name."""
        registry = get_circuit_breaker_registry()
        cb = registry.get("unknown")

        assert cb is None

    def test_get_all_status(self):
        """get_all_status should return status for all breakers."""
        registry = get_circuit_breaker_registry()
        registry.get_or_create("test1")
        registry.get_or_create("test2")

        statuses = registry.get_all_status()

        assert len(statuses) == 2
        names = {s["name"] for s in statuses}
        assert names == {"test1", "test2"}

    def test_reset_all(self):
        """reset_all() should reset all breakers to CLOSED."""
        registry = get_circuit_breaker_registry()
        cb1 = registry.get_or_create("test1")
        cb2 = registry.get_or_create("test2")

        cb1.force_open()
        cb2.force_open()

        registry.reset_all()

        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_circuit_breaker(self):
        """create_circuit_breaker should create breaker with custom config."""
        cb = create_circuit_breaker(
            "custom",
            failure_threshold=10,
            success_threshold=3,
            timeout_seconds=60.0,
        )

        assert cb.name == "custom"
        assert cb.config.failure_threshold == 10
        assert cb.config.success_threshold == 3
        assert cb.config.timeout_seconds == 60.0

    def test_create_circuit_breaker_with_exclude_exceptions(self):
        """create_circuit_breaker should support exclude_exceptions."""
        cb = create_circuit_breaker(
            "custom_exclude",
            exclude_exceptions=(ValueError, KeyError),
        )

        assert ValueError in cb.config.exclude_exceptions
        assert KeyError in cb.config.exclude_exceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
