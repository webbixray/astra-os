"""Agent hierarchy and communication system."""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .agent import (
    Agent,
    AgentContext,
    AgentMessage,
    AgentRegistry,
    AgentResult,
    AgentType,
    get_agent_registry,
)
from .events import EventBus, get_event_bus
from .memory import MemoryManager

logger = logging.getLogger(__name__)


class HandoffType(str, Enum):
    """Types of agent handoffs."""

    DELEGATION = "delegation"  # Parent delegates to child
    ESCALATION = "escalation"  # Child escalates to parent
    PEER = "peer"  # Between same-level agents
    SPECIALIST = "specialist"  # To domain specialist


@dataclass
class HandoffRequest:
    """Request to hand off work to another agent."""

    from_agent: UUID
    to_agent: UUID | None  # None = let system choose
    handoff_type: HandoffType
    task_description: str
    context: dict[str, Any]
    required_capabilities: list[str] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: int = 300


@dataclass
class HandoffResponse:
    """Response to a handoff request."""

    accepted: bool
    assigned_agent: UUID | None = None
    reason: str | None = None
    estimated_duration_seconds: int | None = None


class CommunicationProtocol:
    """Protocol for agent-to-agent communication."""

    def __init__(self):
        self._message_queues: dict[UUID, asyncio.Queue] = {}
        self._subscriptions: dict[UUID, set[str]] = {}
        self._lock = asyncio.Lock()

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to an agent."""
        async with self._lock:
            if message.to_agent not in self._message_queues:
                self._message_queues[message.to_agent] = asyncio.Queue()

            await self._message_queues[message.to_agent].put(message)
            logger.debug(
                "Message sent from %s to %s: %s",
                message.from_agent,
                message.to_agent,
                message.message_type,
            )
            return True

    async def receive_message(
        self, agent_id: UUID, timeout: float | None = None
    ) -> AgentMessage | None:
        """Receive a message for an agent."""
        async with self._lock:
            if agent_id not in self._message_queues:
                self._message_queues[agent_id] = asyncio.Queue()

        try:
            if timeout:
                return await asyncio.wait_for(self._message_queues[agent_id].get(), timeout=timeout)
            return await self._message_queues[agent_id].get()
        except TimeoutError:
            return None

    async def broadcast(self, message: AgentMessage, agent_ids: list[UUID]) -> int:
        """Broadcast message to multiple agents."""
        sent = 0
        for agent_id in agent_ids:
            broadcast_msg = AgentMessage(
                message_id=uuid4(),
                from_agent=message.from_agent,
                to_agent=agent_id,
                message_type=message.message_type,
                payload=message.payload,
                correlation_id=message.correlation_id,
            )
            if await self.send_message(broadcast_msg):
                sent += 1
        return sent

    def subscribe(self, agent_id: UUID, topic: str) -> None:
        """Subscribe agent to a topic."""
        if agent_id not in self._subscriptions:
            self._subscriptions[agent_id] = set()
        self._subscriptions[agent_id].add(topic)

    def unsubscribe(self, agent_id: UUID, topic: str) -> None:
        """Unsubscribe agent from a topic."""
        if agent_id in self._subscriptions:
            self._subscriptions[agent_id].discard(topic)


class HandoffManager:
    """Manages agent handoffs and delegation."""

    def __init__(
        self,
        registry: AgentRegistry,
        communication: CommunicationProtocol,
        event_bus: EventBus,
        memory_manager: MemoryManager | None = None,
    ):
        self.registry = registry
        self.communication = communication
        self.event_bus = event_bus
        self.memory_manager = memory_manager
        self._pending_handoffs: dict[UUID, HandoffRequest] = {}

    async def request_handoff(self, request: HandoffRequest) -> HandoffResponse:
        """Request handoff to another agent."""
        # If no target agent specified, find best match
        if request.to_agent is None:
            target_agent = await self._find_best_agent(request)
            if not target_agent:
                return HandoffResponse(
                    accepted=False,
                    reason="No suitable agent found with required capabilities",
                )
            request.to_agent = target_agent

        # Store pending handoff
        self._pending_handoffs[request.to_agent] = request

        # Send handoff notification
        message = AgentMessage(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            message_type="handoff_request",
            payload={
                "handoff_type": request.handoff_type.value,
                "task_description": request.task_description,
                "context": request.context,
                "required_capabilities": request.required_capabilities,
                "priority": request.priority,
            },
            correlation_id=uuid4(),
        )

        await self.communication.send_message(message)

        # Wait for response (with timeout)
        try:
            response = await asyncio.wait_for(
                self._wait_for_handoff_response(request.to_agent),
                timeout=request.timeout_seconds,
            )
            return response
        except TimeoutError:
            return HandoffResponse(
                accepted=False,
                reason="Handoff request timed out",
            )

    async def _wait_for_handoff_response(self, to_agent: UUID) -> HandoffResponse:
        """Wait for handoff response from target agent."""
        while True:
            message = await self.communication.receive_message(to_agent, timeout=1.0)
            if message and message.message_type == "handoff_response":
                return HandoffResponse(
                    accepted=message.payload.get("accepted", False),
                    assigned_agent=message.from_agent,
                    reason=message.payload.get("reason"),
                    estimated_duration_seconds=message.payload.get("estimated_duration"),
                )
            await asyncio.sleep(0.1)

    async def _find_best_agent(self, request: HandoffRequest) -> UUID | None:
        """Find the best agent for a handoff based on capabilities."""
        registry = get_agent_registry()

        # Get all available agent types
        agent_types = registry.list_agent_types()

        best_match: AgentType | None = None
        best_score = 0

        for agent_type in agent_types:
            config = registry.get_config(agent_type)
            if not config:
                continue

            # Check if agent has required capabilities
            if all(cap in config.capabilities for cap in request.required_capabilities):
                # Score by number of matching capabilities (higher is better)
                matching = sum(
                    1 for cap in request.required_capabilities if cap in config.capabilities
                )
                if matching > best_score:
                    best_score = matching
                    best_match = agent_type

        if best_match:
            # Create and return the agent instance ID
            agent = registry.create_agent(best_match, request.context.get("tenant_id", uuid4()))
            return agent.agent_id

        return None

    async def handle_handoff_request(self, agent: Agent, message: AgentMessage) -> HandoffResponse:
        """Handle incoming handoff request."""
        payload = message.payload
        required_caps = payload.get("required_capabilities", [])

        # Check if this agent can handle the request
        can_handle = all(cap in agent.config.capabilities for cap in required_caps)

        if not can_handle:
            return HandoffResponse(
                accepted=False,
                reason="Agent does not have required capabilities",
            )

        # Accept handoff
        return HandoffResponse(
            accepted=True,
            assigned_agent=agent.agent_id,
            estimated_duration_seconds=60,
        )

    async def complete_handoff(
        self,
        from_agent: UUID,
        to_agent: UUID,
        result: AgentResult,
    ) -> None:
        """Complete a handoff with result."""
        message = AgentMessage(
            from_agent=to_agent,
            to_agent=from_agent,
            message_type="handoff_complete",
            payload={
                "result": result.model_dump() if hasattr(result, "model_dump") else str(result),
                "success": result.success if hasattr(result, "success") else True,
            },
            correlation_id=uuid4(),
        )
        await self.communication.send_message(message)

        # Clean up pending
        self._pending_handoffs.pop(to_agent, None)


class AgentHierarchy:
    """Manages the agent hierarchy and delegation flow."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._hierarchy: dict[AgentType, list[AgentType]] = self._build_hierarchy()

    def _build_hierarchy(self) -> dict[AgentType, list[AgentType]]:
        """Build the agent hierarchy."""
        return {
            AgentType.CEO: [
                AgentType.MARKETING_DIRECTOR,
                AgentType.CREATIVE_DIRECTOR,
                AgentType.ADVERTISING_DIRECTOR,
                AgentType.RESEARCH_DIRECTOR,
                AgentType.ANALYTICS_DIRECTOR,
                AgentType.WORKFLOW_DIRECTOR,
                AgentType.COMPLIANCE_DIRECTOR,
            ],
            AgentType.MARKETING_DIRECTOR: [
                AgentType.CONTENT_SPECIALIST,
                AgentType.SEO_SPECIALIST,
                AgentType.SOCIAL_SPECIALIST,
            ],
            AgentType.CREATIVE_DIRECTOR: [
                AgentType.COPYWRITER,
                AgentType.DESIGNER,
                AgentType.BRAND_VOICE,
            ],
            AgentType.ADVERTISING_DIRECTOR: [
                AgentType.CAMPAIGN_OPTIMIZER,
                AgentType.BID_MANAGER,
                AgentType.AUDIENCE_RESEARCHER,
            ],
            AgentType.RESEARCH_DIRECTOR: [
                AgentType.MARKET_RESEARCHER,
                AgentType.COMPETITOR_ANALYST,
                AgentType.TREND_ANALYZER,
            ],
            AgentType.ANALYTICS_DIRECTOR: [
                AgentType.DATA_ANALYST,
                AgentType.ATTRIBUTION_MODELER,
                AgentType.REPORT_GENERATOR,
            ],
            AgentType.WORKFLOW_DIRECTOR: [
                AgentType.WORKFLOW_BUILDER,
                AgentType.AUTOMATION_SCHEDULER,
                AgentType.INTEGRATION_MANAGER,
            ],
            AgentType.COMPLIANCE_DIRECTOR: [
                AgentType.CONTENT_REVIEWER,
                AgentType.PRIVACY_AUDITOR,
                AgentType.POLICY_ENFORCER,
            ],
        }

    def get_subordinates(self, agent_type: AgentType) -> list[AgentType]:
        """Get direct subordinates of an agent type."""
        return self._hierarchy.get(agent_type, [])

    def get_supervisor(self, agent_type: AgentType) -> AgentType | None:
        """Get the supervisor of an agent type."""
        for supervisor, subordinates in self._hierarchy.items():
            if agent_type in subordinates:
                return supervisor
        return None

    def get_path_to_root(self, agent_type: AgentType) -> list[AgentType]:
        """Get the path from an agent to the CEO."""
        path = [agent_type]
        current = agent_type
        while current != AgentType.CEO:
            supervisor = self.get_supervisor(current)
            if not supervisor:
                break
            path.append(supervisor)
            current = supervisor
        return path

    def can_delegate(self, from_type: AgentType, to_type: AgentType) -> bool:
        """Check if an agent can delegate to another."""
        # Can delegate to direct subordinates
        if to_type in self.get_subordinates(from_type):
            return True

        # CEO can delegate to anyone
        if from_type == AgentType.CEO:
            return True

        # Cannot delegate up or sideways
        return False

    async def create_team(
        self,
        leader_type: AgentType,
        tenant_id: UUID,
        task: str,
    ) -> list[Agent]:
        """Create a team with leader and appropriate subordinates."""
        registry = get_agent_registry()
        leader = registry.create_agent(leader_type, tenant_id)

        subordinates = self.get_subordinates(leader_type)
        team = [leader]

        for sub_type in subordinates:
            sub_agent = registry.create_agent(sub_type, tenant_id)
            team.append(sub_agent)

        return team


class AgentCoordinator:
    """Coordinates multi-agent workflows."""

    def __init__(
        self,
        hierarchy: AgentHierarchy,
        communication: CommunicationProtocol,
        handoff_manager: HandoffManager,
        event_bus: EventBus,
    ):
        self.hierarchy = hierarchy
        self.communication = communication
        self.handoff = handoff_manager
        self.event_bus = event_bus

    async def execute_parallel(
        self,
        agents: list[Agent],
        inputs: list[Any],
        context: AgentContext,
    ) -> list[AgentResult]:
        """Execute multiple agents in parallel."""

        async def run_agent(agent: Agent, input_data: Any) -> AgentResult:
            sub_context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                parent_context=context,
            )
            return await agent.run(sub_context, input_data)

        tasks = [run_agent(agent, inp) for agent, inp in zip(agents, inputs)]
        return await asyncio.gather(*tasks)

    async def execute_sequential(
        self,
        agents: list[Agent],
        initial_input: Any,
        context: AgentContext,
    ) -> list[AgentResult]:
        """Execute agents sequentially, passing output to next."""
        results = []
        current_input = initial_input

        for agent in agents:
            sub_context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                parent_context=context,
            )
            result = await agent.run(sub_context, current_input)
            results.append(result)
            current_input = result.output

        return results

    async def execute_pipeline(
        self,
        stages: list[list[Agent]],  # Each stage can have multiple agents in parallel
        initial_input: Any,
        context: AgentContext,
    ) -> list[AgentResult]:
        """Execute a multi-stage pipeline."""
        all_results = []
        current_input = initial_input

        for stage_agents in stages:
            if len(stage_agents) == 1:
                result = await stage_agents[0].run(context, current_input)
                results = [result]
            else:
                inputs = [current_input] * len(stage_agents)
                results = await self.execute_parallel(stage_agents, inputs, context)

            all_results.extend(results)
            current_input = [r.output for r in results]

        return all_results


# Global instances (initialized on startup)
_hierarchy: AgentHierarchy | None = None
_coordinator: AgentCoordinator | None = None
_handoff_manager: HandoffManager | None = None


def get_hierarchy(registry: AgentRegistry | None = None) -> AgentHierarchy:
    """Get the global agent hierarchy."""
    global _hierarchy
    if _hierarchy is None:
        _hierarchy = AgentHierarchy(registry or get_agent_registry())
    return _hierarchy


def get_handoff_manager(
    registry: AgentRegistry | None = None,
    event_bus: EventBus | None = None,
    memory_manager: MemoryManager | None = None,
) -> HandoffManager:
    """Get the global handoff manager."""
    global _handoff_manager
    if _handoff_manager is None:
        _handoff_manager = HandoffManager(
            registry or get_agent_registry(),
            CommunicationProtocol(),
            event_bus or get_event_bus(),
            memory_manager,
        )
    return _handoff_manager


def get_coordinator(
    hierarchy: AgentHierarchy | None = None,
    handoff_manager: HandoffManager | None = None,
    event_bus: EventBus | None = None,
) -> AgentCoordinator:
    """Get the global agent coordinator."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator(
            hierarchy or get_hierarchy(),
            CommunicationProtocol(),
            handoff_manager or get_handoff_manager(),
            event_bus or get_event_bus(),
        )
    return _coordinator
