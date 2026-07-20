"""OpenTelemetry tracing setup for Agent Orchestrator."""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_TRACER: trace.Tracer | None = None
_TRACER_PROVIDER: TracerProvider | None = None


def init_tracing(
    service_name: str = "astra-agent-orchestrator",
    otlp_endpoint: str | None = None,
) -> trace.Tracer:
    """Initialize OpenTelemetry tracing with optional OTLP exporter.

    Args:
        service_name: Name of the service for resource attributes
        otlp_endpoint: Optional OTLP HTTP endpoint (e.g., http://otel:4318/v1/traces)
                       If None, no exporter is configured (no-op tracing)

    Returns:
        Configured tracer instance

    """
    global _TRACER, _TRACER_PROVIDER

    if _TRACER is not None:
        return _TRACER

    # Create resource with service name
    resource = Resource.create({SERVICE_NAME: service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)
    _TRACER_PROVIDER = provider

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Add OTLP exporter if endpoint provided
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    # Get tracer
    _TRACER = trace.get_tracer(__name__)
    return _TRACER


def get_tracer() -> trace.Tracer:
    """Get the configured tracer, initializing with defaults if needed.

    Returns:
        Configured tracer instance

    """
    global _TRACER

    if _TRACER is None:
        # Initialize with defaults - endpoint can be set via env var
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        _TRACER = init_tracing(
            service_name=os.getenv("OTEL_SERVICE_NAME", "astra-agent-orchestrator"),
            otlp_endpoint=otlp_endpoint,
        )

    return _TRACER


def shutdown_tracing() -> None:
    """Shutdown the tracer provider, flushing any pending spans."""
    global _TRACER, _TRACER_PROVIDER

    if _TRACER_PROVIDER is not None:
        _TRACER_PROVIDER.shutdown()
        _TRACER_PROVIDER = None
        _TRACER = None


# Convenience: get tracer lazily
# TRACER will be initialized on first access via get_tracer()
