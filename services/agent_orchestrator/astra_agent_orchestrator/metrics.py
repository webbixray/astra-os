"""Prometheus metrics for Agent Orchestrator."""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# ============================================================================
# Agent Run Metrics
# ============================================================================

AGENT_RUNS = Counter(
    "agent_runs_total",
    "Total number of agent runs",
    ["agent_type", "success"],
)

AGENT_DURATION = Histogram(
    "agent_duration_seconds",
    "Agent run duration in seconds",
    ["agent_type"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300],
)

AGENT_TOKENS = Counter(
    "agent_tokens_total",
    "Total tokens consumed by agent runs",
    ["agent_type"],
)

AGENT_COST = Counter(
    "agent_cost_usd_total",
    "Total cost in USD for agent runs",
    ["agent_type"],
)

AGENT_ACTIVE = Gauge(
    "agent_active_count",
    "Number of currently running agents",
    ["agent_type"],
)


# ============================================================================
# Tool Call Metrics
# ============================================================================

TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "Total tool calls made by agents",
    ["agent_type", "tool_name", "success"],
)

TOOL_DURATION = Histogram(
    "agent_tool_duration_seconds",
    "Tool call duration in seconds",
    ["agent_type", "tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30],
)


# ============================================================================
# Delegation Metrics
# ============================================================================

DELEGATIONS = Counter(
    "agent_delegations_total",
    "Total delegations from agent to sub-agent",
    ["agent_type", "subagent_type", "success"],
)


# ============================================================================
# Recording Functions
# ============================================================================

def record_agent_run(
    agent_type: str,
    success: bool,
    duration_seconds: float,
    tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """Record metrics for an agent run.
    
    Args:
        agent_type: Type of agent (e.g., "CEO", "CONTENT_SPECIALIST")
        success: Whether the run succeeded
        duration_seconds: Run duration in seconds
        tokens: Total tokens consumed
        cost_usd: Total cost in USD

    """
    AGENT_RUNS.labels(agent_type=agent_type, success=str(success).lower()).inc()
    AGENT_DURATION.labels(agent_type=agent_type).observe(duration_seconds)

    if tokens > 0:
        AGENT_TOKENS.labels(agent_type=agent_type).inc(tokens)

    if cost_usd > 0:
        AGENT_COST.labels(agent_type=agent_type).inc(cost_usd)


def record_tool_call(
    agent_type: str,
    tool_name: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """Record metrics for a tool call.
    
    Args:
        agent_type: Type of agent that made the call
        tool_name: Name of the tool called
        success: Whether the tool call succeeded
        duration_seconds: Call duration in seconds

    """
    TOOL_CALLS.labels(
        agent_type=agent_type,
        tool_name=tool_name,
        success=str(success).lower(),
    ).inc()
    TOOL_DURATION.labels(agent_type=agent_type, tool_name=tool_name).observe(duration_seconds)


def record_delegation(
    agent_type: str,
    subagent_type: str,
    success: bool,
) -> None:
    """Record metrics for a delegation to a sub-agent.
    
    Args:
        agent_type: Type of parent agent
        subagent_type: Type of sub-agent
        success: Whether the delegation succeeded

    """
    DELEGATIONS.labels(
        agent_type=agent_type,
        subagent_type=subagent_type,
        success=str(success).lower(),
    ).inc()


# ============================================================================
# Context Managers for Automatic Metrics
# ============================================================================

@dataclass
class RunTracker:
    """Tracks run state for AgentMetricsContext."""

    success: bool = False
    tokens: int = 0
    cost: float = 0.0
    _entered: bool = False
    _start_time: float = 0.0

    def set_success(self, success: bool, tokens: int = 0, cost: float = 0.0) -> None:
        """Mark the run result."""
        self.success = success
        self.tokens = tokens
        self.cost = cost


@dataclass
class AgentMetricsContext:
    """Context manager for automatic agent run metrics.
    
    Usage:
        with AgentMetricsContext("CEO") as tracker:
            # run agent
            tracker.set_success(True, tokens=100, cost=0.001)
        
    On exit, automatically records run metrics and decrements active gauge.
    """

    agent_type: str
    _tracker: RunTracker = field(default_factory=RunTracker)

    def __enter__(self) -> RunTracker:
        AGENT_ACTIVE.labels(agent_type=self.agent_type).inc()
        self._tracker._entered = True
        self._tracker._start_time = time.monotonic()
        return self._tracker

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._tracker._entered:
            return None

        AGENT_ACTIVE.labels(agent_type=self.agent_type).dec()

        duration = time.monotonic() - self._tracker._start_time

        # If exception occurred and not already marked, it's a failure
        if exc_type is not None and not self._tracker.success:
            self._tracker.success = False

        record_agent_run(
            agent_type=self.agent_type,
            success=self._tracker.success,
            duration_seconds=duration,
            tokens=self._tracker.tokens,
            cost_usd=self._tracker.cost,
        )

        # Don't suppress exceptions
        return False


@contextmanager
def track_agent_run(
    agent_type: str,
    tokens: int = 0,
    cost_usd: float = 0.0,
):
    """Convenience context manager for tracking agent runs.
    
    Usage:
        with track_agent_run("CEO", tokens=100, cost_usd=0.001):
            result = await agent.run(...)
    """
    tracker = RunTracker()
    AGENT_ACTIVE.labels(agent_type=agent_type).inc()
    start = time.monotonic()

    try:
        yield tracker
        tracker.set_success(True, tokens=tokens, cost=cost_usd)
    except Exception:
        tracker.set_success(False)
        raise
    finally:
        duration = time.monotonic() - start
        AGENT_ACTIVE.labels(agent_type=agent_type).dec()
        record_agent_run(
            agent_type=agent_type,
            success=tracker.success,
            duration_seconds=duration,
            tokens=tracker.tokens,
            cost_usd=tracker.cost,
        )


# ============================================================================
# Prometheus Exposition
# ============================================================================

def get_metrics_response() -> tuple[bytes, str]:
    """Get Prometheus metrics in exposition format.
    
    Returns:
        Tuple of (metrics_bytes, content_type)

    """
    return generate_latest(), CONTENT_TYPE_LATEST
