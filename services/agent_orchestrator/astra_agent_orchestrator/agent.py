from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

# OpenTelemetry tracing
from opentelemetry.trace import SpanKind
from pydantic import BaseModel, Field

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from .governance import GovernanceMiddleware
    from .metrics import AgentMetricsContext, record_agent_run, record_delegation, record_tool_call

# Runtime imports for default parameter values
from .metrics import AgentMetricsContext, record_agent_run, record_delegation, record_tool_call
from .tools import (
    ExecutionSandbox,
    Tool,
    ToolRegistry,
    default_sandbox,
    tool_registry,
)

logger = logging.getLogger(__name__)

# Tracer instance for this module - lazy initialization
_TRACER = None


def get_tracer_instance():
    global _TRACER
    if _TRACER is None:
        from .telemetry import get_tracer

        _TRACER = get_tracer()
    return _TRACER


# RAG pipeline type — imported lazily to avoid circular deps
class _RAGPipelineStub:
    """Lazy proxy for RagPipeline to avoid import at module level."""

    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    async def search(self, query: str, organization_id: UUID, **kwargs: Any) -> list[Any]:
        return await self._pipeline.search(query, organization_id, **kwargs)

    async def assemble_context(self, query: str, organization_id: UUID, **kwargs: Any) -> Any:
        return await self._pipeline.assemble_context(query, organization_id, **kwargs)


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
        parent_context: AgentContext | None = None,
    ):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.session_id = session_id or uuid4()
        self.parent_context = parent_context
        self.metadata: dict[str, Any] = {}
        self.created_at = datetime.now(UTC)
        self.trace_id = uuid4()

    def child_context(self, agent_id: UUID) -> AgentContext:
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
    sub_agent_results: list[AgentResult] = Field(default_factory=list)
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
        self.tenant_id = config.tenant_id if hasattr(config, "tenant_id") else None
        self.tool_registry = tool_registry
        self.sandbox = sandbox
        self.state = AgentState.INITIALIZING
        self.context: AgentContext | None = None
        self._governance_middleware = None
        self._rag_pipeline = None
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

    @abstractmethod
    async def reason(self, context: AgentContext, observation: Any) -> Any:
        """Reason about the current state and decide next action."""

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

        # Use metrics context manager to track active agents
        with AgentMetricsContext(self.agent_type.value) as metrics_ctx:
            # Start OpenTelemetry span for agent run with semantic conventions
            with get_tracer_instance().start_as_current_span(
                f"agent.{self.agent_type.value}.run",
                kind=SpanKind.INTERNAL,
                attributes={
                    "service.name": "astra-agent-orchestrator",
                    "agent.astra.id": str(self.agent_id),
                    "agent.astra.type": self.agent_type.value,
                    "agent.astra.autonomy_level": self.config.autonomy_level,
                    "agent.astra.tenant_id": str(self.tenant_id) if self.tenant_id else "",
                    "agent.astra.session_id": str(context.session_id) if context.session_id else "",
                },
            ) as span:
                try:
                    self.state = AgentState.RUNNING
                    result = await self.execute(context, input_data)
                    self.state = AgentState.COMPLETED

                    # Record success metrics on span
                    span.set_attribute("agent.success", result.success)
                    span.set_attribute("agent.duration_ms", result.duration_ms)
                    span.set_attribute("agent.tokens_used", result.tokens_used)
                    span.set_attribute("agent.cost_usd", result.cost_usd)
                    span.set_attribute("agent.iterations", result.iterations)
                    if result.error:
                        span.set_attribute("agent.error", result.error)

                    # Record Prometheus metrics
                    record_agent_run(
                        agent_type=self.agent_type.value,
                        success=result.success,
                        duration_seconds=result.duration_ms / 1000.0,
                        tokens=result.tokens_used,
                        cost_usd=result.cost_usd,
                    )

                    # Update metrics context
                    metrics_ctx.tokens = result.tokens_used
                    metrics_ctx.cost = result.cost_usd
                    metrics_ctx.success = result.success

                    return result
                except Exception as e:
                    self.state = AgentState.FAILED
                    span.record_exception(e)
                    span.set_attribute("agent.success", False)
                    span.set_attribute("agent.error", str(e))

                    # Add trace context to exception log
                    trace_ctx = get_trace_context()
                    logger.exception(
                        "Agent %s failed: %s",
                        self.agent_id,
                        e,
                        extra=trace_ctx,
                    )
                    return AgentResult(
                        agent_id=self.agent_id,
                        success=False,
                        error=str(e),
                        duration_ms=duration_ms,
                        iterations=self._iteration,
                    )
                finally:
                    self._record_metrics()

    def _record_metrics(self) -> None:
        duration_ms = int((time.time() - self._start_time) * 1000)
        logger.info(
            "Agent %s completed in %dms, iterations: %d, tools: %d",
            self.agent_id,
            duration_ms,
            self._iteration,
            len(self._tool_calls),
        )

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: AgentContext | None = None,
    ) -> ToolResult:
        """Execute a tool through the registry, with governance enforcement.

        If a GovernanceMiddleware is configured, the tool call is checked
        against autonomy rules before execution. Blocked calls return an
        error result without executing the tool.
        """
        self.state = AgentState.WAITING_FOR_TOOL

        # Governance check — if middleware is configured
        governance = getattr(self, "_governance_middleware", None)
        if governance is not None:
            check_result = governance.check_tool_call(tool_name, parameters)
            if check_result.blocked:
                logger.warning(
                    "Agent %s tool call '%s' BLOCKED by governance: %s",
                    self.agent_id,
                    tool_name,
                    check_result.reason,
                )
                # Add governance block event to span
                span.add_event(
                    "governance.blocked",
                    {
                        "tool.name": tool_name,
                        "reason": check_result.reason,
                        "agent.autonomy_level": self.config.autonomy_level,
                    },
                )
                self.state = AgentState.WAITING_FOR_APPROVAL
                call = ToolCall(tool_name=tool_name, parameters=parameters)
                self._tool_calls.append(call)
                result = ToolResult(
                    call_id=call.call_id,
                    tool_name=tool_name,
                    success=False,
                    error=f"Governance BLOCKED: {check_result.reason}",
                )
                self._tool_results.append(result)
                self.state = AgentState.RUNNING
                return result

            if check_result.requires_approval and not check_result.blocked:
                logger.info(
                    "Agent %s tool call '%s' requires approval: %s",
                    self.agent_id,
                    tool_name,
                    check_result.reason,
                )
                # Add governance approval required event to span
                span.add_event(
                    "governance.approval_required",
                    {
                        "tool.name": tool_name,
                        "reason": check_result.reason,
                    },
                )
                # In SEMI_AUTO mode, log but still execute low-risk tools
                # The approval is tracked for audit purposes

        call = ToolCall(tool_name=tool_name, parameters=parameters)
        self._tool_calls.append(call)

        # OpenTelemetry span for tool call with semantic conventions
        with get_tracer_instance().start_as_current_span(
            f"agent.{self.agent_type.value}.call_tool",
            kind=SpanKind.CLIENT,
            attributes={
                "service.name": "astra-agent-orchestrator",
                "agent.id": str(self.agent_id),
                "agent.type": self.agent_type.value,
                "tool.name": tool_name,
            },
        ) as span:
            start = time.time()
            try:
                result_data = await self.tool_registry.execute_tool(tool_name, parameters, context)
                duration_ms = int((time.time() - start) * 1000)
                duration_seconds = duration_ms / 1000.0

                result = ToolResult(
                    call_id=call.call_id,
                    tool_name=tool_name,
                    success=result_data.get("success", False),
                    result=result_data.get("result"),
                    error=result_data.get("error"),
                    duration_ms=duration_ms,
                )

                # Record on span with events
                if result.success:
                    span.add_event(
                        "tool.call.completed",
                        {
                            "tool.name": tool_name,
                            "duration_ms": duration_ms,
                        },
                    )
                else:
                    span.add_event(
                        "tool.call.failed",
                        {
                            "tool.name": tool_name,
                            "error": result.error,
                            "duration_ms": duration_ms,
                        },
                    )

                span.set_attribute("tool.success", result.success)
                span.set_attribute("tool.duration_ms", duration_ms)
                if result.error:
                    span.set_attribute("tool.error", result.error)

                # Record Prometheus metrics
                record_tool_call(
                    agent_type=self.agent_type.value,
                    tool_name=tool_name,
                    success=result.success,
                    duration_seconds=duration_seconds,
                )

                self._tool_results.append(result)
                self.state = AgentState.RUNNING
                return result
            except Exception as e:
                duration_ms = int((time.time() - start) * 1000)
                span.add_event(
                    "tool.call.exception",
                    {
                        "tool.name": tool_name,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                span.record_exception(e)
                span.set_attribute("tool.success", False)
                span.set_attribute("tool.error", str(e))

                record_tool_call(
                    agent_type=self.agent_type.value,
                    tool_name=tool_name,
                    success=False,
                    duration_seconds=duration_ms / 1000.0,
                )
                raise

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

        # OpenTelemetry span for delegation with semantic conventions
        with get_tracer_instance().start_as_current_span(
            f"agent.{self.agent_type.value}.delegate",
            kind=SpanKind.INTERNAL,
            attributes={
                "service.name": "astra-agent-orchestrator",
                "agent.id": str(self.agent_id),
                "agent.type": self.agent_type.value,
                "subagent.type": subagent_type.value,
                "subagent.id": str(subagent.agent_id),
            },
        ) as span:
            try:
                result = await subagent.run(sub_context, input_data)

                # Add delegation success event
                span.add_event(
                    "agent.delegation.completed",
                    {
                        "subagent.id": str(subagent.agent_id),
                        "subagent.type": subagent_type.value,
                        "success": result.success,
                        "duration_ms": result.duration_ms,
                    },
                )

                span.set_attribute("subagent.success", result.success)
                span.set_attribute("subagent.duration_ms", result.duration_ms)

                # Record Prometheus metrics
                record_delegation(
                    agent_type=self.agent_type.value,
                    subagent_type=subagent_type.value,
                    success=result.success,
                )

                self._sub_agent_results.append(result)
                return result
            except Exception as e:
                span.add_event(
                    "agent.delegation.failed",
                    {
                        "subagent.id": str(subagent.agent_id),
                        "subagent.type": subagent_type.value,
                        "error": str(e),
                    },
                )
                span.set_attribute("subagent.success", False)
                span.set_attribute("subagent.error", str(e))

                record_delegation(
                    agent_type=self.agent_type.value,
                    subagent_type=subagent_type.value,
                    success=False,
                )
                raise

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

    def set_governance(self, middleware: GovernanceMiddleware) -> None:
        """Attach a governance middleware to this agent.

        Once set, all tool calls will be checked against the governance
        config before execution.
        """
        self._governance_middleware = middleware

    def get_governance_log(self) -> list[dict[str, Any]]:
        """Get the governance action log from the middleware."""
        governance = getattr(self, "_governance_middleware", None)
        if governance:
            return governance.get_action_log()
        return []

    # ------------------------------------------------------------------
    # RAG / Knowledge integration
    # ------------------------------------------------------------------

    def set_rag_pipeline(self, pipeline: Any) -> None:
        """Attach a RAG pipeline to this agent.

        Once set, the agent can query the knowledge graph for context
        before making decisions.
        """
        self._rag_pipeline = pipeline

    async def get_rag_context(
        self,
        query: str,
        organization_id: UUID,
        **kwargs: Any,
    ) -> Any | None:
        """Assemble RAG context for the current query.

        Returns a RAGContext object with search results, memory context,
        and brand guidelines, or None if no pipeline is attached.
        """
        if self._rag_pipeline is None:
            return None
        try:
            return await self._rag_pipeline.assemble_context(
                query=query,
                organization_id=organization_id,
                agent_id=str(self.agent_id),
                **kwargs,
            )
        except Exception:
            logger.exception("RAG context assembly failed for agent %s", self.agent_id)
            return None

    async def search_knowledge(
        self,
        query: str,
        organization_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the knowledge graph for relevant information.

        Returns a list of search result dicts, or empty list if no
        pipeline is attached or search fails.
        """
        if self._rag_pipeline is None:
            return []
        try:
            results = await self._rag_pipeline.search(
                query=query,
                organization_id=organization_id,
                limit=limit,
            )
            return [
                {
                    "node_id": r.node_id,
                    "name": r.name,
                    "description": r.description[:200],
                    "score": round(r.score, 3),
                    "relevance": r.relevance_label,
                }
                for r in results
            ]
        except Exception:
            logger.exception("Knowledge search failed for agent %s", self.agent_id)
            return []

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
            AgentType.MARKETING_DIRECTOR,
            AgentType.CREATIVE_DIRECTOR,
            AgentType.ADVERTISING_DIRECTOR,
            AgentType.RESEARCH_DIRECTOR,
            AgentType.ANALYTICS_DIRECTOR,
            AgentType.WORKFLOW_DIRECTOR,
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
