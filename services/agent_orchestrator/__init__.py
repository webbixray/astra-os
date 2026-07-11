"""Agent Orchestrator Runtime Package."""

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
from .events import (
    Event,
    EventBus,
    EventStore,
    get_event_bus,
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
from .tools import (
    ExecutionSandbox,
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    default_sandbox,
    tool_registry,
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
from .comms import (
    AgentAuditTrail,
    AgentTraceEntry,
    RedisMessageBus,
    get_agent_audit_trail,
    get_redis_message_bus,
)

# Concrete agent implementations (lazy to avoid circular imports)
# Import from services.agent_orchestrator.agents directly:
#   from services.agent_orchestrator.agents import CEOAgent, DirectorAgent, SpecialistAgent

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
]

__version__ = "0.1.0"