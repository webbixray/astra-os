"""Integration tests for the agent pipeline.

These tests exercise the full agent execution flow:
- Agent creation via registry
- ReAct loop execution (mocked LLM)
- CEO → Director → Specialist delegation chain
- Event bus integration
- Audit trail recording
- Memory manager operations (in-memory mode)
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from astra_agent_orchestrator.agent import (
    AgentContext,
    AgentMessage,
    AgentRegistry,
    AgentResult,
    AgentType,
)
from astra_agent_orchestrator.agents import CEOAgent, DirectorAgent, SpecialistAgent
from astra_agent_orchestrator.comms import (
    AgentAuditTrail,
    AgentTraceEntry,
)
from astra_agent_orchestrator.events import Event, EventBus
from astra_agent_orchestrator.hierarchy import (
    AgentCoordinator,
    AgentHierarchy,
    CommunicationProtocol,
    HandoffManager,
)
from astra_agent_orchestrator.memory import MemoryManager
from astra_agent_orchestrator.router import (
    ModelProvider,
    ModelResponse,
    ModelRouterFacade,
)
from astra_agent_orchestrator.tools import (
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_router(
    response_text: str = '{"thought":"test","action":null,"action_input":null,"final_answer":"done"}',
) -> ModelRouterFacade:
    """Create a ModelRouterFacade that returns a canned response."""
    facade = MagicMock(spec=ModelRouterFacade)
    facade.generate = AsyncMock(
        return_value=ModelResponse(
            content=response_text,
            model_id="test-model-id",
            model_name="test-model",
            provider=ModelProvider.OPENAI,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            cost_usd=0.001,
        )
    )
    facade.stream_generate = AsyncMock()
    facade.embed = AsyncMock(return_value=[0.1] * 1536)
    facade.health_check_all = AsyncMock(return_value={})
    facade.get_all_stats = AsyncMock(return_value={})
    facade.get_available_providers = AsyncMock(return_value=[])
    facade.close = AsyncMock()
    return facade


def _make_ceo_agent(tenant_id: uuid.UUID | None = None) -> CEOAgent:
    """Create a CEO agent with mocked model router."""
    tid = tenant_id or uuid.uuid4()
    agent = CEOAgent(tenant_id=tid)
    agent._router = _make_mock_router()
    return agent


def _make_director_agent(
    agent_type: AgentType = AgentType.MARKETING_DIRECTOR,
    tenant_id: uuid.UUID | None = None,
) -> DirectorAgent:
    """Create a Director agent with mocked model router."""
    tid = tenant_id or uuid.uuid4()
    agent = DirectorAgent(agent_type=agent_type, tenant_id=tid)
    agent._router = _make_mock_router()
    return agent


def _make_specialist_agent(
    agent_type: AgentType = AgentType.CONTENT_SPECIALIST,
    tenant_id: uuid.UUID | None = None,
) -> SpecialistAgent:
    """Create a Specialist agent with mocked model router."""
    tid = tenant_id or uuid.uuid4()
    agent = SpecialistAgent(agent_type=agent_type, tenant_id=tid)
    agent._router = _make_mock_router()
    return agent


# ---------------------------------------------------------------------------
# Test: Agent Registry Integration
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    """Test that the registry creates all agent types correctly."""

    def test_registry_creates_all_director_types(self):
        registry = AgentRegistry()
        directors = [
            AgentType.MARKETING_DIRECTOR,
            AgentType.CREATIVE_DIRECTOR,
            AgentType.ADVERTISING_DIRECTOR,
            AgentType.RESEARCH_DIRECTOR,
            AgentType.ANALYTICS_DIRECTOR,
            AgentType.WORKFLOW_DIRECTOR,
            AgentType.COMPLIANCE_DIRECTOR,
        ]
        for dt in directors:
            agent = registry.create_agent(dt, uuid.uuid4())
            assert agent is not None
            assert isinstance(agent, DirectorAgent)

    def test_registry_creates_all_specialist_types(self):
        registry = AgentRegistry()
        specialists = [
            AgentType.CONTENT_SPECIALIST,
            AgentType.SEO_SPECIALIST,
            AgentType.SOCIAL_SPECIALIST,
            AgentType.COPYWRITER,
            AgentType.DESIGNER,
            AgentType.BRAND_VOICE,
            AgentType.CAMPAIGN_OPTIMIZER,
            AgentType.BID_MANAGER,
            AgentType.AUDIENCE_RESEARCHER,
            AgentType.MARKET_RESEARCHER,
            AgentType.COMPETITOR_ANALYST,
            AgentType.TREND_ANALYZER,
            AgentType.DATA_ANALYST,
            AgentType.ATTRIBUTION_MODELER,
            AgentType.REPORT_GENERATOR,
            AgentType.WORKFLOW_BUILDER,
            AgentType.AUTOMATION_SCHEDULER,
            AgentType.INTEGRATION_MANAGER,
            AgentType.CONTENT_REVIEWER,
            AgentType.PRIVACY_AUDITOR,
            AgentType.POLICY_ENFORCER,
        ]
        for st in specialists:
            agent = registry.create_agent(st, uuid.uuid4())
            assert agent is not None
            assert isinstance(agent, SpecialistAgent)

    def test_registry_creates_ceo(self):
        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.CEO, uuid.uuid4())
        assert isinstance(agent, CEOAgent)


# ---------------------------------------------------------------------------
# Test: ReAct Loop Execution
# ---------------------------------------------------------------------------


class TestReActLoop:
    """Test the ReAct execution loop end-to-end."""

    @pytest.mark.asyncio
    async def test_ceo_single_iteration_final_answer(self):
        """CEO receives a task and returns a final answer in one iteration."""
        agent = _make_ceo_agent()
        # Patch the router on the agent
        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=_make_mock_router(),
        ):
            context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            result = await agent.run(
                context,
                {"objective": "Launch a Q3 marketing campaign", "context": {"budget": 50000}},
            )

        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.output is not None
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_ceo_multi_iteration_with_tool_call(self):
        """CEO executes a tool call then returns final answer."""
        # First response: tool call; second: final answer
        responses = [
            json.dumps(
                {
                    "thought": "I need to search for market data",
                    "action": "web_search",
                    "action_input": {"query": "Q3 marketing trends"},
                    "final_answer": None,
                }
            ),
            json.dumps(
                {
                    "thought": "Got the data, now decomposing",
                    "action": None,
                    "action_input": None,
                    "final_answer": "Campaign plan ready",
                }
            ),
        ]
        call_count = 0

        async def mock_generate(request):
            nonlocal call_count
            resp = ModelResponse(
                content=responses[min(call_count, len(responses) - 1)],
                model_id="test-model-id",
                model_name="test-model",
                provider=ModelProvider.OPENAI,
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                cost_usd=0.001,
            )
            call_count += 1
            return resp

        facade = MagicMock(spec=ModelRouterFacade)
        facade.generate = mock_generate

        agent = _make_ceo_agent()

        # Register a mock tool
        class _SearchTool(Tool):
            def __init__(self):
                super().__init__(
                    definition=ToolDefinition(
                        name="web_search",
                        description="Search the web",
                        parameters=[
                            ToolParameter(
                                name="query", type="string", description="q", required=True
                            )
                        ],
                    )
                )

            async def execute(self, query: str = "", **kw):
                return {"results": [{"title": f"Result for {query}"}]}

        agent._tool_registry = ToolRegistry()
        agent._tool_registry.register(_SearchTool())

        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=facade,
        ):
            context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            result = await agent.run(context, "Research Q3 trends")

        assert result.success is True
        assert len(result.tool_calls) >= 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_specialist_single_iteration(self):
        """Specialist receives a task and completes in one iteration."""
        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=_make_mock_router(
                '{"thought":"Simple task","action":null,"action_input":null,"final_answer":"Content created"}'
            ),
        ):
            agent = _make_specialist_agent()
            context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            result = await agent.run(context, "Write a blog post about AI marketing")

        assert result.success is True
        assert "Content created" in result.output

    @pytest.mark.asyncio
    async def test_director_preparation(self):
        """Director prepares input with subordinate list."""
        agent = _make_director_agent(AgentType.MARKETING_DIRECTOR)
        prompt = agent.prepare_input({"task": "Launch social campaign"})
        assert "social campaign" in prompt
        assert "content_specialist" in prompt.lower() or "CONTENT_SPECIALIST" in prompt

    @pytest.mark.asyncio
    async def test_max_iterations_stops(self):
        """Agent stops after max_iterations even without final answer."""
        # Always return an action (never final_answer)
        action_response = json.dumps(
            {
                "thought": "Keep going",
                "action": "web_search",
                "action_input": {"query": "test"},
                "final_answer": None,
            }
        )

        async def mock_generate(request):
            return ModelResponse(
                content=action_response,
                model_id="test-model-id",
                model_name="test-model",
                provider=ModelProvider.OPENAI,
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                cost_usd=0.001,
            )

        facade = MagicMock(spec=ModelRouterFacade)
        facade.generate = mock_generate

        agent = _make_ceo_agent()
        agent.config.max_iterations = 3

        # Register a mock tool
        class _SearchTool(Tool):
            def __init__(self):
                super().__init__(
                    definition=ToolDefinition(
                        name="web_search",
                        description="Search",
                        parameters=[
                            ToolParameter(
                                name="query", type="string", description="q", required=True
                            )
                        ],
                    )
                )

            async def execute(self, query: str = "", **kw):
                return "result"

        agent._tool_registry = ToolRegistry()
        agent._tool_registry.register(_SearchTool())

        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=facade,
        ):
            context = AgentContext(
                agent_id=agent.agent_id,
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            result = await agent.run(context, "test")

        assert result.iterations == 3
        assert "Max iterations" in result.output


# ---------------------------------------------------------------------------
# Test: Event Bus Integration
# ---------------------------------------------------------------------------


class TestEventBusIntegration:
    """Test event bus with agent lifecycle events."""

    @pytest.mark.asyncio
    async def test_agent_execution_publishes_events(self):
        """Verify events can be published and received during agent execution."""
        bus = EventBus()
        received_events: list[Event] = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe("agent.started", handler)
        await bus.subscribe("agent.completed", handler)

        # Publish lifecycle events
        await bus.publish(
            Event(event_type="agent.started", source="test-agent", payload={"task": "test"})
        )
        await bus.publish(
            Event(event_type="agent.completed", source="test-agent", payload={"result": "done"})
        )

        assert len(received_events) == 2
        assert received_events[0].event_type == "agent.started"
        assert received_events[1].event_type == "agent.completed"

    @pytest.mark.asyncio
    async def test_wildcard_subscription_receives_all(self):
        bus = EventBus()
        all_events: list[Event] = []

        async def handler(event: Event):
            all_events.append(event)

        await bus.subscribe_all(handler)
        await bus.publish(Event(event_type="agent.started", source="a"))
        await bus.publish(Event(event_type="tool.called", source="b"))
        await bus.publish(Event(event_type="agent.completed", source="a"))

        assert len(all_events) == 3

    @pytest.mark.asyncio
    async def test_event_history_retention(self):
        bus = EventBus()
        for i in range(5):
            await bus.publish(Event(event_type=f"type_{i}", source="test"))

        history = bus.get_history()
        assert len(history) == 5
        assert history[0].event_type == "type_0"

    @pytest.mark.asyncio
    async def test_event_history_filtering(self):
        bus = EventBus()
        await bus.publish(Event(event_type="agent.started", source="agent_a"))
        await bus.publish(Event(event_type="tool.called", source="agent_b"))
        await bus.publish(Event(event_type="agent.started", source="agent_b"))

        filtered = bus.get_history(event_type="agent.started")
        assert len(filtered) == 2


# ---------------------------------------------------------------------------
# Test: Communication Protocol
# ---------------------------------------------------------------------------


class TestCommunicationProtocol:
    """Test in-memory communication protocol."""

    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        comm = CommunicationProtocol()
        sender = uuid.uuid4()
        receiver = uuid.uuid4()

        msg = AgentMessage(
            from_agent=sender,
            to_agent=receiver,
            message_type="task",
            payload={"task": "do something"},
        )

        await comm.send_message(msg)
        received = await comm.receive_message(receiver, timeout=1.0)

        assert received is not None
        assert received.from_agent == sender
        assert received.message_type == "task"

    @pytest.mark.asyncio
    async def test_broadcast(self):
        comm = CommunicationProtocol()
        sender = uuid.uuid4()
        receivers = [uuid.uuid4() for _ in range(3)]

        msg = AgentMessage(
            from_agent=sender,
            to_agent=receivers[0],
            message_type="broadcast",
            payload={"info": "hello"},
        )

        sent = await comm.broadcast(msg, receivers)
        assert sent == 3

        # Each receiver should have a message
        for r in receivers:
            received = await comm.receive_message(r, timeout=1.0)
            assert received is not None

    @pytest.mark.asyncio
    async def test_topic_subscription(self):
        comm = CommunicationProtocol()
        agent_id = uuid.uuid4()
        comm.subscribe(agent_id, "campaign.updates")
        assert "campaign.updates" in comm._subscriptions[agent_id]

        comm.unsubscribe(agent_id, "campaign.updates")
        assert "campaign.updates" not in comm._subscriptions.get(agent_id, set())


# ---------------------------------------------------------------------------
# Test: Memory Manager (in-memory mode)
# ---------------------------------------------------------------------------


class TestMemoryManager:
    """Test memory manager without external dependencies."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_in_memory(self):
        """MemoryManager stores and retrieves without PG/Redis (no-op)."""
        manager = MemoryManager()  # no pg_pool, no redis
        agent_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        entry = await manager.store(
            agent_id=agent_id,
            tenant_id=tenant_id,
            memory_type="working",
            key="test_key",
            value={"data": "hello"},
            importance=0.8,
        )

        assert entry.key == "test_key"
        assert entry.importance == 0.8
        assert entry.memory_type == "working"

    @pytest.mark.asyncio
    async def test_memory_consolidation_noop(self):
        """Consolidation with no PG is a no-op."""
        manager = MemoryManager()
        count = await manager.consolidate(uuid.uuid4(), uuid.uuid4())
        assert count == 0

    @pytest.mark.asyncio
    async def test_memory_stats_empty(self):
        """Stats with no PG returns defaults."""
        manager = MemoryManager()
        stats = await manager.get_stats()
        assert stats["working"] == 0
        assert stats["episodic"] == 0
        assert stats["semantic"] == 0

    @pytest.mark.asyncio
    async def test_forget_noop(self):
        """Forget with no PG returns 0."""
        manager = MemoryManager()
        count = await manager.forget(memory_id=uuid.uuid4())
        assert count == 0


# ---------------------------------------------------------------------------
# Test: Audit Trail
# ---------------------------------------------------------------------------


class TestAuditTrail:
    """Test audit trail buffering and flushing."""

    def test_trace_entry_creation(self):
        entry = AgentTraceEntry(
            agent_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            agent_type="ceo",
            agent_name="CEO Agent",
            iteration=1,
            thought="Analyzing objective",
            action=None,
            final_answer="Plan ready",
        )
        assert entry.agent_type == "ceo"
        assert entry.iteration == 1
        assert entry.success is True

    @pytest.mark.asyncio
    async def test_audit_trail_buffering(self):
        """Entries are buffered when no PG pool."""
        trail = AgentAuditTrail()  # no pg_pool
        entry = await trail.record_step(
            agent_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            agent_type="director",
            agent_name="Marketing Director",
            iteration=1,
            thought="Decomposing task",
            action="delegate",
        )
        assert entry.thought == "Decomposing task"

        # Flush with no PG should clear buffer
        flushed = await trail.flush()
        assert flushed == 1  # 1 entry was buffered and flushed (no-op)

    @pytest.mark.asyncio
    async def test_audit_trail_record_completion(self):
        trail = AgentAuditTrail()
        result = AgentResult(
            agent_id=uuid.uuid4(),
            success=True,
            output="Campaign plan ready",
            tool_calls=[],
            tool_results=[],
            tokens_used=150,
            cost_usd=0.005,
            duration_ms=1200,
            iterations=3,
        )
        entry = await trail.record_completion(
            agent_id=result.agent_id,
            tenant_id=uuid.uuid4(),
            agent_type="ceo",
            agent_name="CEO Agent",
            result=result,
        )
        assert entry.final_answer == "Campaign plan ready"
        assert entry.tokens_used == 150
        assert entry.cost_usd == 0.005


# ---------------------------------------------------------------------------
# Test: Hierarchy Integration
# ---------------------------------------------------------------------------


class TestHierarchyIntegration:
    """Test the full hierarchy with agent creation."""

    def test_hierarchy_builds_correctly(self):
        registry = AgentRegistry()
        hierarchy = AgentHierarchy(registry)

        # CEO should have 7 direct reports
        ceo_subs = hierarchy.get_subordinates(AgentType.CEO)
        assert len(ceo_subs) == 7

        # Marketing Director should have 3 specialists
        md_subs = hierarchy.get_subordinates(AgentType.MARKETING_DIRECTOR)
        assert len(md_subs) == 3

    def test_path_to_root(self):
        registry = AgentRegistry()
        hierarchy = AgentHierarchy(registry)
        path = hierarchy.get_path_to_root(AgentType.CONTENT_SPECIALIST)
        assert path[0] == AgentType.CONTENT_SPECIALIST
        assert AgentType.MARKETING_DIRECTOR in path
        assert path[-1] == AgentType.CEO

    def test_delegation_rules(self):
        registry = AgentRegistry()
        hierarchy = AgentHierarchy(registry)

        # CEO can delegate to anyone
        assert hierarchy.can_delegate(AgentType.CEO, AgentType.CONTENT_SPECIALIST)

        # Marketing Director can delegate to its specialists
        assert hierarchy.can_delegate(AgentType.MARKETING_DIRECTOR, AgentType.CONTENT_SPECIALIST)

        # Marketing Director cannot delegate to another director's specialist
        assert not hierarchy.can_delegate(AgentType.MARKETING_DIRECTOR, AgentType.COPYWRITER)

    @pytest.mark.asyncio
    async def test_create_team(self):
        registry = AgentRegistry()
        hierarchy = AgentHierarchy(registry)
        team = await hierarchy.create_team(
            AgentType.MARKETING_DIRECTOR,
            uuid.uuid4(),
            "Launch campaign",
        )
        # Should include director + 3 specialists
        assert len(team) == 4
        assert isinstance(team[0], DirectorAgent)
        for member in team[1:]:
            assert isinstance(member, SpecialistAgent)


# ---------------------------------------------------------------------------
# Test: Handoff Manager
# ---------------------------------------------------------------------------


class TestHandoffManager:
    """Test handoff request/response flow."""

    @pytest.mark.asyncio
    async def test_handle_handoff_request_accepts(self):
        registry = AgentRegistry()
        comm = CommunicationProtocol()
        bus = EventBus()
        manager = HandoffManager(registry, comm, bus)

        agent = registry.create_agent(AgentType.CONTENT_SPECIALIST, uuid.uuid4())
        msg = AgentMessage(
            from_agent=uuid.uuid4(),
            to_agent=agent.agent_id,
            message_type="handoff_request",
            payload={"required_capabilities": ["content_creation"]},
        )

        response = await manager.handle_handoff_request(agent, msg)
        assert response.accepted is True

    @pytest.mark.asyncio
    async def test_handle_handoff_request_rejects(self):
        registry = AgentRegistry()
        comm = CommunicationProtocol()
        bus = EventBus()
        manager = HandoffManager(registry, comm, bus)

        agent = registry.create_agent(AgentType.CONTENT_SPECIALIST, uuid.uuid4())
        msg = AgentMessage(
            from_agent=uuid.uuid4(),
            to_agent=agent.agent_id,
            message_type="handoff_request",
            payload={"required_capabilities": ["quantum_computing"]},  # not a real capability
        )

        response = await manager.handle_handoff_request(agent, msg)
        assert response.accepted is False


# ---------------------------------------------------------------------------
# Test: Coordinator Execution Modes
# ---------------------------------------------------------------------------


class TestCoordinatorExecution:
    """Test AgentCoordinator parallel/sequential/pipeline execution."""

    @pytest.mark.asyncio
    async def test_execute_sequential(self):
        """Sequential execution passes output of one agent to the next."""
        registry = AgentRegistry()
        comm = CommunicationProtocol()
        bus = EventBus()
        hierarchy = AgentHierarchy(registry)
        handoff = HandoffManager(registry, comm, bus)
        coordinator = AgentCoordinator(hierarchy, comm, handoff, bus)

        agent1 = _make_specialist_agent(AgentType.CONTENT_SPECIALIST)
        agent2 = _make_specialist_agent(AgentType.SEO_SPECIALIST)

        # Patch routers
        response1 = '{"thought":"creating","action":null,"action_input":null,"final_answer":"Blog post written"}'
        response2 = '{"thought":"optimizing","action":null,"action_input":null,"final_answer":"SEO complete"}'

        call_count = 0

        async def mock_generate(request):
            nonlocal call_count
            text = response1 if call_count == 0 else response2
            call_count += 1
            return ModelResponse(
                content=text,
                model_id="test-id",
                model_name="test",
                provider=ModelProvider.OPENAI,
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                cost_usd=0.001,
            )

        facade = MagicMock(spec=ModelRouterFacade)
        facade.generate = mock_generate

        for a in [agent1, agent2]:
            a._router = facade

        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=facade,
        ):
            context = AgentContext(
                agent_id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            results = await coordinator.execute_sequential(
                [agent1, agent2], "Write and optimize blog post", context
            )

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True

    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        """Parallel execution runs all agents concurrently."""
        registry = AgentRegistry()
        comm = CommunicationProtocol()
        bus = EventBus()
        hierarchy = AgentHierarchy(registry)
        handoff = HandoffManager(registry, comm, bus)
        coordinator = AgentCoordinator(hierarchy, comm, handoff, bus)

        agents = [
            _make_specialist_agent(AgentType.CONTENT_SPECIALIST),
            _make_specialist_agent(AgentType.SEO_SPECIALIST),
            _make_specialist_agent(AgentType.SOCIAL_SPECIALIST),
        ]

        response = (
            '{"thought":"done","action":null,"action_input":null,"final_answer":"Task complete"}'
        )

        async def mock_generate(request):
            return ModelResponse(
                content=response,
                model_id="test-id",
                model_name="test",
                provider=ModelProvider.OPENAI,
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                cost_usd=0.001,
            )

        facade = MagicMock(spec=ModelRouterFacade)
        facade.generate = mock_generate

        for a in agents:
            a._router = facade

        with patch(
            "astra_agent_orchestrator.agents.base.get_model_router_facade",
            return_value=facade,
        ):
            context = AgentContext(
                agent_id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
            results = await coordinator.execute_parallel(
                agents, ["task1", "task2", "task3"], context
            )

        assert len(results) == 3
        for r in results:
            assert r.success is True
