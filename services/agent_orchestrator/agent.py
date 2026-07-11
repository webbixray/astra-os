"""Agent Registry and Base Agent Class."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .tools import (
    ExecutionSandbox,
    Tool,
    ToolRegistry,
    default_sandbox,
    tool_registry,
)

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent types in the hierarchy."""

    CEO = "CEO"
    MARKETING_DIRECTOR = "MARKETING_DIRECTOR"
    CREATIVE_DIRECTOR = "CREATIVE_DIRECTOR"
    ADVERTISING_DIRECTOR = "ADVERTISING_DIRECTOR"
    RESEARCH_DIRECTOR = "RESEARCH_DIRECTOR"
    ANALYTICS_DIRECTOR = "ANALYTICS_DIRECTOR"
    WORKFLOW_DIRECTOR = "WORKFLOW_DIRECTOR"
    COMPLIANCE_DIRECTOR = "COMPLIANCE_DIRECTOR"
    CONTENT_SPECIALIST = "CONTENT_SPECIALIST"
    SEO_SPECIALIST = "SEO_SPECIALIST"
    SOCIAL_SPECIALIST = "SOCIAL_SPECIALIST"
    COPYWRITER = "COPYWRITER"
    DESIGNER = "DESIGNER"
    BRAND_VOICE = "BRAND_VOICE"
    CAMPAIGN_OPTIMIZER = "CAMPAIGN_OPTIMIZER"
    BID_MANAGER = "BID_MANAGER"
    AUDIENCE_RESEARCHER = "AUDIENCE_RESEARCHER"
    MARKET_RESEARCHER = "MARKET_RESEARCHER"
    COMPETITOR_ANALYST = "COMPETITOR_ANALYST"
    TREND_ANALYZER = "TREND_ANALYZER"
    DATA_ANALYST = "DATA_ANALYST"
    ATTRIBUTION_MODELER = "ATTRIBUTION_MODELER"
    REPORT_GENERATOR = "REPORT_GENERATOR"
    WORKFLOW_BUILDER = "WORKFLOW_BUILDER"
    AUTOMATION_SCHEDULER = "AUTOMATION_SCHEDULER"
    INTEGRATION_MANAGER = "INTEGRATION_MANAGER"
    CONTENT_REVIEWER = "CONTENT_REVIEWER"
    PRIVACY_AUDITOR = "PRIVACY_AUDITOR"
    POLICY_ENFORCER = "POLICY_ENFORCER"
    KNOWLEDGE_GRAPH_OPERATOR = "KNOWLEDGE_GRAPH_OPERATOR"
    BRAND_MEMORY_CURATOR = "BRAND_MEMORY_CURATOR"
    PERFORMANCE_HISTORIAN = "PERFORMANCE_HISTORIAN"


class AgentState(str, Enum):
    """Agent runtime state."""

    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_SUBAGENT = "WAITING_FOR_SUBAGENT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


@dataclass
class AgentConfig:
    """Agent configuration."""

    agent_id: UUID = field(default_factory=uuid4)
    agent_type: AgentType = AgentType.CEO
    name: str = ""
    description: str = ""
    parent_agent_id: UUID | None = None
    capabilities: list[str] = field(default_factory=list)
    model_config: dict[str, Any] = field(default_factory=dict)
    autonomy_level: int = 0  # 0=advisory, 1=semi-auto, 2=full-auto
    max_iterations: int = 10
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: str = ""
    tool_config: dict[str, Any] = field(default_factory=dict)
    sandbox_config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tenant_id: UUID | None = None


class AgentContext:
    """Execution context for an agent."""

    def __init__(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        parent_context: "AgentContext | None" = None,
    ):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.session_id = session_id or uuid4()
        self.parent_context = parent_context
        self.metadata: dict[str, Any] = {}
        self.created_at = datetime.now(UTC)
        self.trace_id = uuid4()

    def child_context(self, agent_id: UUID) -> "AgentContext":
        """Create a child context for a sub-agent."""
        return AgentContext(
            agent_id=agent_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            session_id=self.session_id,
            parent_context=self,
        )


class ToolCall(BaseModel):
    """A tool call request."""

    tool_name: str
    parameters: dict[str, Any]
    call_id: UUID = Field(default_factory=uuid4)


class ToolResult(BaseModel):
    """A tool execution result."""

    call_id: UUID
    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0


class AgentMessage(BaseModel):
    """Message between agents."""

    message_id: UUID = Field(default_factory=uuid4)
    from_agent: UUID
    to_agent: UUID
    message_type: str  # request, response, notification, handoff
    payload: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID | None = None


class AgentResult(BaseModel):
    """Result of agent execution."""

    agent_id: UUID
    success: bool
    output: Any = None
    error: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    sub_agent_results: list["AgentResult"] = Field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    iterations: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Agent(ABC):
    """Base agent class."""

    def __init__(
        self,
        config: AgentConfig,
        tenant_id: UUID,
        tool_registry: ToolRegistry = tool_registry,
        sandbox: ExecutionSandbox = default_sandbox,
    ):
        self.config = config
        self.tenant_id = config.tenant_id if hasattr(config, 'tenant_id') else None
        self.tool_registry = tool_registry
        self.sandbox = sandbox
        self.state = AgentState.INITIALIZING
        self.context: AgentContext | None = None
        self._iteration = 0
        self._start_time: float = 0
        self._tool_calls: list[ToolCall] = []
        self._tool_results: list[ToolResult] = []
        self._sub_agent_results: list[AgentResult] = []
        self._tokens_used = 0
        self._cost_usd = 0.0

    @property
    def agent_id(self) -> UUID:
        return self.config.agent_id

    @property
    def agent_type(self) -> AgentType:
        return self.config.agent_type

    @abstractmethod
    async def execute(self, context: AgentContext, input_data: Any) -> AgentResult:
        """Execute the agent's main logic."""
        pass

    @abstractmethod
    async def reason(self, context: AgentContext, observation: Any) -> Any:
        """Reason about the current state and decide next action."""
        pass

    async def initialize(self, context: AgentContext) -> None:
        """Initialize the agent before execution."""
        self.context = context
        self.state = AgentState.IDLE
        logger.info("Agent %s (%s) initialized", self.agent_id, self.agent_type)

    async def run(self, context: AgentContext, input_data: Any) -> AgentResult:
        """Run the agent with the given input."""
        await self.initialize(context)
        self._start_time = time.time()
        self._iteration = 0
        self._tool_calls = []
        self._tool_results = []
        self._sub_agent_results = []

        try:
            self.state = AgentState.RUNNING
            result = await self.execute(context, input_data)
            self.state = AgentState.COMPLETED
            return result
        except Exception as e:
            self.state = AgentState.FAILED
            logger.exception("Agent %s failed: %s", self.agent_id, e)
            return AgentResult(
                agent_id=self.agent_id,
                success=False,
                error=str(e),
                duration_ms=int((time.time() - self._start_time) * 1000),
                iterations=self._iteration,
            )
        finally:
            self._record_metrics()

    def _record_metrics(self) -> None:
        duration_ms = int((time.time() - self._start_time) * 1000)
        logger.info(
            "Agent %s completed in %dms, iterations: %d, tools: %d",
            self.agent_id, duration_ms, self._iteration, len(self._tool_calls)
        )

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: AgentContext | None = None,
    ) -> ToolResult:
        """Execute a tool through the registry."""
        self.state = AgentState.WAITING_FOR_TOOL
        call = ToolCall(tool_name=tool_name, parameters=parameters)
        self._tool_calls.append(call)

        start = time.time()
        result_data = await self.tool_registry.execute_tool(
            tool_name, parameters, context
        )
        duration_ms = int((time.time() - start) * 1000)

        result = ToolResult(
            call_id=call.call_id,
            tool_name=tool_name,
            success=result_data.get("success", False),
            result=result_data.get("result"),
            error=result_data.get("error"),
            duration_ms=duration_ms,
        )
        self._tool_results.append(result)
        self.state = AgentState.RUNNING
        return result

    async def delegate_to_subagent(
        self,
        subagent_type: AgentType,
        input_data: Any,
        context: AgentContext | None = None,
    ) -> AgentResult:
        """Delegate a task to a sub-agent."""
        self.state = AgentState.WAITING_FOR_SUBAGENT

        # Use the global registry singleton
        registry = get_agent_registry()
        subagent = registry.create_agent(subagent_type, self.tenant_id)

        sub_context = context.child_context(subagent.agent_id) if context else context
        result = await subagent.run(sub_context, input_data)

        self._sub_agent_results.append(result)
        return result

    async def request_approval(
        self,
        action: str,
        details: dict[str, Any],
        context: AgentContext,
    ) -> bool:
        """Request human approval for an action."""
        self.state = AgentState.WAITING_FOR_APPROVAL
        # In real implementation, would send to approval system
        # For now, auto-approve based on autonomy level
        return self.config.autonomy_level >= 1

    async def run_code(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute code in sandbox."""
        return await self.sandbox.execute_python(code, globals_dict)

    async def run_command(
        self,
        command: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute a shell command in sandbox."""
        return await self.sandbox.execute_command(command, cwd, env)

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools in OpenAI function format."""
        return self.tool_registry.get_tool_openai_functions()

    def get_tool(self, tool_name: str) -> Tool | None:
        return self.tool_registry.get_tool(tool_name)


class AgentRegistry:
    """Registry for creating and managing agents."""

    def __init__(self):
        self._agent_configs: dict[AgentType, AgentConfig] = {}
        self._agent_classes: dict[AgentType, type[Agent]] = {}
        self._instances: dict[UUID, Agent] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Register default agent configurations."""
        # CEO Agent
        self.register_agent_type(
            AgentType.CEO,
            AgentConfig(
                agent_type=AgentType.CEO,
                name="CEO Agent",
                description="Strategic orchestrator that decomposes high-level goals and delegates to directors",
                capabilities=["planning", "delegation", "strategy", "decision_making"],
                autonomy_level=2,
                system_prompt="""You are the CEO Agent of ASTRA OS. Your role is to:
1. Understand high-level business objectives
2. Decompose them into actionable plans for directors
3. Delegate tasks to appropriate directors
4. Monitor progress and make strategic decisions
5. Ensure alignment with organizational goals
You have full autonomy to delegate and make strategic decisions.""",
            ),
        )

        # Marketing Director
        self.register_agent_type(
            AgentType.MARKETING_DIRECTOR,
            AgentConfig(
                agent_type=AgentType.MARKETING_DIRECTOR,
                name="Marketing Director",
                description="Orchestrates marketing strategy and delegates to content, SEO, and social specialists",
                capabilities=["planning", "delegation", "campaign_strategy", "brand_management"],
                autonomy_level=1,
                system_prompt="""You are the Marketing Director. Orchestrate marketing campaigns by delegating to:
- Content Specialist (blog posts, articles, copy)
- SEO Specialist (keyword research, optimization)
- Social Media Specialist (social posts, engagement)
Coordinate campaigns, set strategy, review outputs.""",
            ),
        )

        # Creative Director
        self.register_agent_type(
            AgentType.CREATIVE_DIRECTOR,
            AgentConfig(
                agent_type=AgentType.CREATIVE_DIRECTOR,
                name="Creative Director",
                description="Oversees creative output and brand voice consistency",
                capabilities=["brand_voice", "design_review", "creative_direction", "approval"],
                autonomy_level=1,
                system_prompt="""You are the Creative Director. Ensure all creative output:
1. Aligns with brand voice and guidelines
2. Maintains quality standards
3. Is approved before publication
Review and approve content from Copywriter, Designer, Brand Voice agents.""",
            ),
        )

        # Add more default configurations as needed...

    def register_agent_type(
        self,
        agent_type: AgentType,
        config: AgentConfig,
        agent_class: type[Agent] | None = None,
    ) -> None:
        """Register an agent type with its configuration and class."""
        self._agent_configs[agent_type] = config
        if agent_class:
            self._agent_classes[agent_type] = agent_class

    def create_agent(
        self,
        agent_type: AgentType,
        tenant_id: UUID,
        config_overrides: dict[str, Any] | None = None,
    ) -> Agent:
        """Create an agent instance using the appropriate concrete class."""
        config = self._agent_configs.get(agent_type)
        if config is None:
            # Auto-register with a default config derived from the agent type
            config = AgentConfig(
                agent_type=agent_type,
                name=agent_type.value.replace("_", " ").title(),
                description=f"Agent for {agent_type.value}",
                autonomy_level=1,
            )
            self._agent_configs[agent_type] = config

        # Apply overrides
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        config.tenant_id = tenant_id

        # Use registered class if available, otherwise resolve concrete class
        agent_class = self._agent_classes.get(agent_type)
        if agent_class is not None:
            agent = agent_class(config=config, tenant_id=tenant_id)
        else:
            agent = self._create_concrete_agent(agent_type, config, tenant_id)

        self._instances[agent.config.agent_id] = agent
        return agent

    @staticmethod
    def _create_concrete_agent(
        agent_type: AgentType,
        config: AgentConfig,
        tenant_id: UUID,
    ) -> Agent:
        """Create the appropriate concrete agent for a given type.

        Uses lazy imports to avoid circular dependencies.
        If the config has no system_prompt or capabilities (auto-registered),
        the concrete agent will use its own built-in defaults.
        """
        from .agents.ceo import CEOAgent
        from .agents.director import DirectorAgent
        from .agents.specialist import SpecialistAgent

        # If config was auto-registered (no system_prompt, no capabilities),
        # let the concrete agent use its own defaults by passing config=None
        use_defaults = not config.system_prompt and not config.capabilities

        if agent_type == AgentType.CEO:
            return CEOAgent(
                config=config if not use_defaults else None,
                tenant_id=tenant_id,
            )

        director_types = {
            AgentType.MARKETING_DIRECTOR, AgentType.CREATIVE_DIRECTOR,
            AgentType.ADVERTISING_DIRECTOR, AgentType.RESEARCH_DIRECTOR,
            AgentType.ANALYTICS_DIRECTOR, AgentType.WORKFLOW_DIRECTOR,
            AgentType.COMPLIANCE_DIRECTOR,
        }
        if agent_type in director_types:
            return DirectorAgent(
                agent_type=agent_type,
                config=config if not use_defaults else None,
                tenant_id=tenant_id,
            )

        return SpecialistAgent(
            agent_type=agent_type,
            config=config if not use_defaults else None,
            tenant_id=tenant_id,
        )

    def get_agent(self, agent_id: UUID) -> Agent | None:
        return self._instances.get(agent_id)

    def get_config(self, agent_type: AgentType) -> AgentConfig | None:
        return self._agent_configs.get(agent_type)

    def list_agent_types(self) -> list[AgentType]:
        return list(self._agent_configs.keys())


# Global registry instance
_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry