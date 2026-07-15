"""Tests for telemetry module."""

from unittest.mock import MagicMock, patch

import pytest
from services.telemetry import (
    get_tracer,
    init_tracing,
    shutdown_tracing,
)


class TestTelemetry:
    """Tests for OpenTelemetry tracing setup."""

    def setup_method(self):
        """Reset global state before each test."""
        from astra_agent_orchestrator import telemetry as telemetry_module
        telemetry_module._TRACER = None
        telemetry_module._TRACER_PROVIDER = None

    def teardown_method(self):
        """Clean up after each test."""
        shutdown_tracing()

    def test_init_tracing_creates_tracer_provider_with_endpoint(self):
        """init_tracing with endpoint should create provider and add span processor."""
        with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
            mock_provider = MagicMock()
            mock_trace.TracerProvider.return_value = mock_provider
            mock_trace.get_tracer.return_value = MagicMock()
            mock_trace.SpanProcessor = MagicMock()

            tracer = init_tracing("test-service", "http://otel:4318/v1/traces")

            assert tracer is not None
            mock_trace.TracerProvider.assert_called_once()
            mock_provider.add_span_processor.assert_called_once()

    def test_init_tracing_without_endpoint_creates_provider_no_exporter(self):
        """init_tracing without endpoint should create provider but no OTLP exporter."""
        with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
            mock_provider = MagicMock()
            mock_trace.TracerProvider.return_value = mock_provider
            mock_trace.get_tracer.return_value = MagicMock()

            tracer = init_tracing("test-service", None)

            assert tracer is not None
            mock_trace.TracerProvider.assert_called_once()
            # Should NOT add span processor when no endpoint
            mock_provider.add_span_processor.assert_not_called()

    def test_init_tracing_sets_global_provider(self):
        """init_tracing should set the global tracer provider."""
        with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
            mock_provider = MagicMock()
            mock_trace.TracerProvider.return_value = mock_provider
            mock_trace.get_tracer.return_value = MagicMock()

            init_tracing("test-service", "http://otel:4318/v1/traces")

            mock_trace.set_tracer_provider.assert_called_once_with(mock_provider)

    def test_get_tracer_returns_same_instance(self):
        """get_tracer should return the same tracer instance."""
        with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_trace.TracerProvider.return_value = MagicMock()

            tracer1 = get_tracer()
            tracer2 = get_tracer()

            assert tracer1 is tracer2
            assert tracer1 is mock_tracer

    def test_get_tracer_initializes_with_defaults_if_needed(self):
        """get_tracer should initialize with defaults if not already initialized."""
        with patch("services.agent_orchestrator.telemetry.init_tracing") as mock_init:
            mock_init.return_value = MagicMock()

            # Force re-initialization
            from astra_agent_orchestrator import telemetry as telemetry_module
            telemetry_module._TRACER = None

            get_tracer()

            mock_init.assert_called_once_with("astra-agent-orchestrator", None)

    def test_shutdown_tracing_calls_provider_shutdown(self):
        """shutdown_tracing should call shutdown on provider."""
        with patch("services.agent_orchestrator.telemetry.trace") as mock_trace:
            mock_provider = MagicMock()
            mock_trace.TracerProvider.return_value = mock_provider
            mock_trace.get_tracer.return_value = MagicMock()

            init_tracing("test-service", "http://otel:4318/v1/traces")
            shutdown_tracing()

            mock_provider.shutdown.assert_called_once()

    def test_shutdown_tracing_handles_none_provider(self):
        """shutdown_tracing should handle None provider gracefully."""
        from astra_agent_orchestrator import telemetry as telemetry_module
        telemetry_module._TRACER_PROVIDER = None

        # Should not raise
        shutdown_tracing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
