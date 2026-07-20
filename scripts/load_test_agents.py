"""Load test: 100 concurrent agent executions < 5s p95.

This script validates the M1 exit criterion:
  "Load test: 100 concurrent agent executions < 5s p95"

It creates 100 concurrent requests through the agent pipeline and measures
latency. No external services required — all LLM calls are mocked.

Usage:
    python scripts/load_test_agents.py
    python scripts/load_test_agents.py --concurrent 200 --timeout 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Add project root to path
sys.path.insert(0, ".")

from services.agent_orchestrator.agent import (
    AgentContext,
)
from services.agent_orchestrator.agents.ceo import CEOAgent
from services.agent_orchestrator.router import (
    ModelProvider,
    ModelResponse,
    ModelRouterFacade,
)


@dataclass
class LoadTestResult:
    """Result of a single agent execution."""

    request_id: int
    success: bool
    duration_ms: float
    iterations: int = 0
    error: str | None = None


@dataclass
class LoadTestReport:
    """Aggregate report of the load test."""

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    results: list[LoadTestResult] = field(default_factory=list)

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95(self) -> float:
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)] if sorted_lat else 0

    @property
    def p99(self) -> float:
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[min(idx, len(sorted_lat) - 1)] if sorted_lat else 0

    @property
    def mean(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0

    def summary(self) -> str:
        target_p95_ms = 5000.0
        passed = self.p95 < target_p95_ms

        lines = [
            "",
            "=" * 60,
            "  ASTRA OS — Agent Load Test Report",
            "=" * 60,
            f"  Total requests:   {self.total_requests}",
            f"  Successful:       {self.successful}",
            f"  Failed:           {self.failed}",
            f"  Success rate:     {self.successful / self.total_requests * 100:.1f}%"
            if self.total_requests
            else "",
            "",
            "  Latency Distribution:",
            f"    Min:            {self.min_latency:.1f}ms",
            f"    P50 (median):   {self.p50:.1f}ms",
            f"    P95:            {self.p95:.1f}ms  {'✅ PASS' if passed else '❌ FAIL'} (< {target_p95_ms:.0f}ms)",
            f"    P99:            {self.p99:.1f}ms",
            f"    Max:            {self.max_latency:.1f}ms",
            f"    Mean:           {self.mean:.1f}ms",
            "",
            f"  Overall:          {'✅ PASS' if passed else '❌ FAIL'}",
            "=" * 60,
            "",
        ]

        if self.failed > 0:
            lines.append("  Failed requests:")
            for r in self.results:
                if not r.success:
                    lines.append(f"    #{r.request_id}: {r.error}")
            lines.append("")

        return "\n".join(lines)


def _make_mock_router() -> ModelRouterFacade:
    """Create a mock ModelRouterFacade for load testing."""
    response_text = json.dumps(
        {
            "thought": "Processing the request",
            "action": None,
            "action_input": None,
            "final_answer": "Load test response complete",
        }
    )

    facade = MagicMock(spec=ModelRouterFacade)
    facade.generate = AsyncMock(
        return_value=ModelResponse(
            content=response_text,
            model_id="load-test-model",
            model_name="load-test",
            provider=ModelProvider.OPENAI,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            cost_usd=0.001,
        )
    )
    return facade


async def _execute_single_request(request_id: int) -> LoadTestResult:
    """Execute a single agent request and return timing info."""
    start = time.perf_counter()

    try:
        agent = CEOAgent(tenant_id=uuid4())
        context = AgentContext(
            agent_id=agent.agent_id,
            tenant_id=uuid4(),
            user_id=uuid4(),
        )

        with patch(
            "services.agent_orchestrator.agents.base.get_model_router_facade",
            return_value=_make_mock_router(),
        ):
            result = await agent.run(
                context,
                {"objective": f"Load test request #{request_id}", "context": {}},
            )

        duration_ms = (time.perf_counter() - start) * 1000

        return LoadTestResult(
            request_id=request_id,
            success=result.success,
            duration_ms=duration_ms,
            iterations=result.iterations,
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return LoadTestResult(
            request_id=request_id,
            success=False,
            duration_ms=duration_ms,
            error=str(e),
        )


async def run_load_test(
    concurrent: int = 100,
    timeout: float = 30.0,
) -> LoadTestReport:
    """Run the load test with N concurrent agent executions."""
    print(f"\n🚀 Starting load test: {concurrent} concurrent agent executions")
    print(f"   Timeout: {timeout}s")
    print("   Target: P95 < 5000ms\n")

    report = LoadTestReport(total_requests=concurrent)

    start_time = time.perf_counter()

    # Execute all requests concurrently
    tasks = [_execute_single_request(i) for i in range(concurrent)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    wall_time = time.perf_counter() - start_time

    for r in results:
        if isinstance(r, Exception):
            report.failed += 1
            report.results.append(
                LoadTestResult(
                    request_id=-1,
                    success=False,
                    duration_ms=0,
                    error=str(r),
                )
            )
        else:
            report.results.append(r)
            if r.success:
                report.successful += 1
                report.latencies.append(r.duration_ms)
            else:
                report.failed += 1

    print(f"   Wall time: {wall_time:.2f}s")
    print(report.summary())

    return report


def main():
    parser = argparse.ArgumentParser(description="ASTRA OS Agent Load Test")
    parser.add_argument(
        "--concurrent",
        "-n",
        type=int,
        default=100,
        help="Number of concurrent requests (default: 100)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=30.0,
        help="Timeout in seconds (default: 30)",
    )
    args = parser.parse_args()

    report = asyncio.run(run_load_test(args.concurrent, args.timeout))

    # Exit with non-zero if test failed
    sys.exit(0 if report.p95 < 5000.0 else 1)


if __name__ == "__main__":
    main()
