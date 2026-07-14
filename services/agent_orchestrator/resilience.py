"""Circuit breaker and resilience patterns for Agent Orchestrator."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"      # Normal operation, calls go through
    OPEN = "open"          # Failing, calls rejected immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitOpenError(Exception):
    """Raised when circuit breaker is OPEN and rejects a call."""

    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s"
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes in HALF_OPEN before closing
    timeout_seconds: float = 30.0       # Time in OPEN before HALF_OPEN
    exclude_exceptions: tuple = ()      # Exception types that don't count as failures


@dataclass
class CircuitBreaker:
    """Circuit breaker with three states:
    - CLOSED: Normal operation, failures counted
    - OPEN: Short-circuiting, rejecting calls with CircuitOpenError
    - HALF_OPEN: Testing recovery, limited calls allowed
    """

    name: str
    config: CircuitBreakerConfig
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)
    _half_open_lock: Lock = field(default_factory=Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current state, auto-transition from OPEN to HALF_OPEN if timeout elapsed."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.config.timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def success_count(self) -> int:
        return self._success_count

    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # Reset on success

    def _record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN immediately reopens
                self._state = CircuitState.OPEN
                self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN

    def _should_reject(self) -> float | None:
        """Check if call should be rejected. Returns retry_after if so."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed < self.config.timeout_seconds:
                    return self.config.timeout_seconds - elapsed
                # Timeout elapsed, will transition to HALF_OPEN on next state check
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return None

    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async callable to execute
            *args, **kwargs: Arguments passed to func
            
        Returns:
            Result of func(*args, **kwargs)
            
        Raises:
            CircuitOpenError: If circuit is OPEN
            Exception: Any exception raised by func (after recording failure)

        """
        # Check if should reject
        retry_after = self._should_reject()
        if retry_after is not None:
            raise CircuitOpenError(self.name, retry_after)

        # Use separate lock for HALF_OPEN to limit concurrent probe calls
        if self.state == CircuitState.HALF_OPEN:
            # Allow one probe at a time in HALF_OPEN
            if not self._half_open_lock.acquire(blocking=False):
                raise CircuitOpenError(self.name, 0.1)
            try:
                return await self._execute_with_recording(func, *args, **kwargs)
            finally:
                self._half_open_lock.release()
        else:
            return await self._execute_with_recording(func, *args, **kwargs)

    async def _execute_with_recording(
        self, func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> Any:
        """Execute function and record success/failure."""
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.exclude_exceptions:
            # Excluded exceptions don't count as failures
            self._record_success()
            raise
        except Exception:
            self._record_failure()
            raise

    def reset(self) -> None:
        """Manually reset circuit to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0.0

    def force_open(self) -> None:
        """Manually force circuit to OPEN state."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.monotonic()

    def get_status(self) -> dict:
        """Get circuit breaker status for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout_seconds": self.config.timeout_seconds,
                }
            }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get_or_create(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get existing breaker or create new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name, config or CircuitBreakerConfig()
                )
            return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        """Get breaker by name."""
        with self._lock:
            return self._breakers.get(name)

    def get_all_status(self) -> list[dict]:
        """Get status of all registered breakers."""
        with self._lock:
            return [b.get_status() for b in self._breakers.values()]

    def reset_all(self) -> None:
        """Reset all breakers to CLOSED."""
        with self._lock:
            for b in self._breakers.values():
                b.reset()


# Global registry instance
_circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return _circuit_breaker_registry


def create_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout_seconds: float = 30.0,
    exclude_exceptions: tuple = (),
) -> CircuitBreaker:
    """Factory function to create a circuit breaker with custom config."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout_seconds=timeout_seconds,
        exclude_exceptions=exclude_exceptions,
    )
    return _circuit_breaker_registry.get_or_create(name, config)
