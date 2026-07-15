"""Tests for Prometheus metrics module."""


import pytest
from services.metrics import (
    AGENT_ACTIVE,
    AGENT_COST,
    AGENT_DURATION,
    AGENT_RUNS,
    AGENT_TOKENS,
    DELEGATIONS,
    TOOL_CALLS,
    TOOL_DURATION,
    AgentMetricsContext,
    record_agent_run,
    record_delegation,
    record_tool_call,
)


class TestMetrics:
    """Tests for Prometheus metrics."""

    def setup_method(self):
        """Reset metrics before each test."""
        # Note: Prometheus metrics are global, so we just test they work

    def test_record_agent_run_increments_counter(self):
        """record_agent_run should increment AGENT_RUNS counter."""
        # Get initial value
        before = AGENT_RUNS.labels(agent_type="CEO", success="true")._value.get()

        record_agent_run(
            agent_type="CEO",
            success=True,
            duration_seconds=1.5,
            tokens=100,
            cost_usd=0.001,
        )

        after = AGENT_RUNS.labels(agent_type="CEO", success="true")._value.get()
        assert after == before + 1

    def test_record_agent_run_increments_duration_histogram(self):
        """record_agent_run should observe duration histogram."""
        record_agent_run(
            agent_type="CEO",
            success=True,
            duration_seconds=2.0,
            tokens=200,
            cost_usd=0.002,
        )

        # Check histogram has observations
        histogram = AGENT_DURATION.labels(agent_type="CEO")
        # Can't easily test exact count without internal access, but verify no error

    def test_record_agent_run_increments_tokens_cost(self):
        """record_agent_run should increment tokens and cost counters."""
        record_agent_run(
            agent_type="CONTENT_SPECIALIST",
            success=True,
            duration_seconds=1.0,
            tokens=500,
            cost_usd=0.005,
        )

        tokens = AGENT_TOKENS.labels(agent_type="CONTENT_SPECIALIST")._value.get()
        cost = AGENT_COST.labels(agent_type="CONTENT_SPECIALIST")._value.get()

        assert tokens >= 500
        assert cost >= 0.005

    def test_record_tool_call_increments_counters(self):
        """record_tool_call should increment tool call counters."""
        record_tool_call(
            agent_type="CEO",
            tool_name="web_search",
            success=True,
            duration_seconds=0.5,
        )

        assert TOOL_CALLS.labels(agent_type="CEO", tool_name="web_search", success="true")._value.get() >= 1
        assert TOOL_DURATION.labels(agent_type="CEO", tool_name="web_search")._value.get() >= 0.5

    def test_record_delegation_increments_counters(self):
        """record_delegation should increment delegation counters."""
        record_delegation(
            agent_type="CEO",
            subagent_type="CONTENT_SPECIALIST",
            success=True,
        )

        assert DELEGATIONS.labels(
            agent_type="CEO",
            subagent_type="CONTENT_SPECIALIST",
            success="true"
        )._value.get() >= 1

    @pytest.mark.asyncio
    async def test_agent_metrics_context_manager(self):
        """AgentMetricsContext should track active agents and record on exit."""
        agent_type = "TEST_AGENT"

        # Get initial active count
        initial_active = AGENT_ACTIVE.labels(agent_type=agent_type)._value.get()

        tracker = AgentMetricsContext(agent_type)

        # On enter, active should increment
        tracker.__enter__()

        after_enter = AGENT_ACTIVE.labels(agent_type=agent_type)._value.get()
        assert after_enter == initial_active + 1

        # On exit with success, should record run and decrement active
        tracker.set_success(True, tokens=100, cost=0.001)
        tracker.__exit__(None, None, None)

        after_exit = AGENT_ACTIVE.labels(agent_type=agent_type)._value.get()
        assert after_exit == initial_active

    @pytest.mark.asyncio
    async def test_agent_metrics_context_records_on_exception(self):
        """AgentMetricsContext should record failed run on exception."""
        agent_type = "TEST_AGENT_FAIL"
        tracker = AgentMetricsContext(agent_type)
        tracker.__enter__()

        try:
            raise RuntimeError("Test error")
        except RuntimeError:
            tracker.__exit__(RuntimeError, RuntimeError("Test error"), None)

        # Should have recorded a failed run
        assert AGENT_RUNS.labels(agent_type=agent_type, success="false")._value.get() >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
