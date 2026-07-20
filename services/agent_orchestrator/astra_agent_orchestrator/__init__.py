"""Agent Orchestrator Runtime Package."""

# Import tests module to make it discoverable
from . import tests
from .agent import (
    Agent,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentRegistry,
    AgentResult,
    AgentState,
    AgentType,
    ToolCall,
    ToolResult,
    get_agent_registry,
)
from .agents import (
    CEOAgent,
    DirectorAgent,
    ReActAgent,
    SpecialistAgent,
)
from .comms import (
    AgentAuditTrail,
    AgentTraceEntry,
    RedisMessageBus,
    get_agent_audit_trail,
    get_redis_message_bus,
)
from .dlq import (
    DeadLetter,
    DeadLetterQueue,
    DLQConsumer,
    create_dlq_consumer,
)
from .events import (
    Event,
    EventBus,
    EventStore,
    get_event_bus,
)
from .governance import (
    GovernanceCheckResult,
    GovernanceMiddleware,
)
from .hierarchy import (
    AgentCoordinator,
    AgentHierarchy,
    CommunicationProtocol,
    HandoffManager,
    HandoffRequest,
    HandoffResponse,
    HandoffType,
    get_coordinator,
    get_handoff_manager,
    get_hierarchy,
)
from .memory import (
    MemoryEntry,
    MemoryManager,
)
from .metrics import (
    AgentMetricsContext,
    RunTracker,
    get_metrics_response,
    record_agent_run,
    record_delegation,
    record_tool_call,
    track_agent_run,
)
from .resilience import (
    Bulkhead,
    BulkheadConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RetryConfig,
    RetryPolicy,
    get_circuit_breaker_registry,
)
from .router import (
    ModelCapability,
    ModelConfig,
    ModelProvider,
    ModelProviderBase,
    ModelRequest,
    ModelResponse,
    ModelRouter,
    StreamingChunk,
    get_model_router,
)
from .supervisor import (
    Supervisor,
    SupervisorConfig,
)
from .telemetry import (
    get_tracer,
    init_tracing,
    shutdown_tracing,
)
from .tools import (
    ExecutionSandbox,
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    default_sandbox,
    tool_registry,
)

# Concrete agent implementations
# Import from astra_agent_orchestrator.agents directly:
#   from astra_agent_orchestrator.agents import CEOAgent, DirectorAgent, SpecialistAgent

__all__ = [
    # Agent
    "Agent",
    "AgentConfig",
    "AgentContext",
    "AgentMessage",
    "AgentRegistry",
    "AgentResult",
    "AgentState",
    "AgentType",
    "ToolCall",
    "ToolResult",
    "get_agent_registry",
    # Events
    "Event",
    "EventBus",
    "EventStore",
    "get_event_bus",
    # Hierarchy
    "AgentCoordinator",
    "AgentHierarchy",
    "CommunicationProtocol",
    "HandoffManager",
    "HandoffRequest",
    "HandoffResponse",
    "HandoffType",
    "get_coordinator",
    "get_handoff_manager",
    "get_hierarchy",
    # Memory
    "MemoryEntry",
    "MemoryManager",
    # Tools
    "ExecutionSandbox",
    "Tool",
    "ToolDefinition",
    "ToolParameter",
    "ToolRegistry",
    "default_sandbox",
    "tool_registry",
    # Router
    "ModelCapability",
    "ModelConfig",
    "ModelProvider",
    "ModelProviderBase",
    "ModelRequest",
    "ModelResponse",
    "ModelRouter",
    "StreamingChunk",
    "get_model_router",
    # Comms & Audit
    "AgentAuditTrail",
    "AgentTraceEntry",
    "RedisMessageBus",
    "get_agent_audit_trail",
    "get_redis_message_bus",
    # Resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "RetryPolicy",
    "RetryConfig",
    "Bulkhead",
    "BulkheadConfig",
    "get_circuit_breaker_registry",
    # Governance
    "GovernanceMiddleware",
    "GovernanceCheckResult",
    # Concrete Agents
    "CEOAgent",
    "DirectorAgent",
    "ReActAgent",
    "SpecialistAgent",
    # DLQ
    "DeadLetterQueue",
    "DeadLetter",
    "DLQConsumer",
    "create_dlq_consumer",
    # Metrics
    "AgentMetricsContext",
    "RunTracker",
    "track_agent_run",
    "record_agent_run",
    "record_delegation",
    "record_tool_call",
    "get_metrics_response",
    # Supervisor
    "Supervisor",
    "SupervisorConfig",
    # Telemetry
    "init_tracing",
    "get_tracer",
    "shutdown_tracing",
    # Governance
    "GovernanceMiddleware",
    "GovernanceCheckResult",
]

__version__ = "0.1.0"
