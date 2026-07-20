from __future__ import annotations

from app.infrastructure.external_adapters.ai.router import UsageRecord, UsageTracker


class TestUsageTracker:
    def setup_method(self):
        UsageTracker._records.clear()

    def test_record_and_summary(self):
        UsageTracker.record(
            UsageRecord(
                provider="openai",
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                duration_ms=500.0,
            )
        )
        UsageTracker.record(
            UsageRecord(
                provider="nvidia_nim",
                model="meta/llama-3.1-70b-instruct",
                input_tokens=200,
                output_tokens=100,
                duration_ms=800.0,
            )
        )
        UsageTracker.record(
            UsageRecord(
                provider="openai",
                model="gpt-4o",
                input_tokens=50,
                output_tokens=30,
                duration_ms=300.0,
                error="timeout",
            )
        )

        summary = UsageTracker.get_cost_summary()
        assert summary["total_calls"] == 3
        assert summary["errors"] == 1
        assert summary["total_tokens"] == 530
        assert summary["total_cost"] > 0

    def test_empty_tracker(self):
        UsageTracker._records.clear()
        summary = UsageTracker.get_cost_summary()
        assert summary["total_calls"] == 0
        assert summary["errors"] == 0
        assert summary["total_cost"] == 0.0

    def test_get_recent(self):
        for _i in range(5):
            UsageTracker.record(UsageRecord(provider="openai", model="gpt-4o-mini"))
        recent = UsageTracker.get_recent(limit=3)
        assert len(recent) == 3

    def test_usage_record_defaults(self):
        record = UsageRecord(provider="openai", model="gpt-4o-mini")
        assert record.input_tokens == 0
        assert record.output_tokens == 0
        assert record.duration_ms == 0.0
        assert record.error is None
        assert record.timestamp > 0
