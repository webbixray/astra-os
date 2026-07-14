"""Tests for agent hierarchy and coordination."""

import uuid

import pytest
from services.agent_orchestrator.agent import (
    AgentMessage,
    AgentRegistry,
    AgentType,
)
from services.agent_orchestrator.events import EventBus
from services.agent_orchestrator.hierarchy import (
    AgentHierarchy,
    CommunicationProtocol,
    HandoffManager,
    HandoffRequest,
    HandoffType,
)


@pytest.fixture
def hierarchy(registry: AgentRegistry) -> AgentHierarchy:
    return AgentHierarchy(registry)


@pytest.fixture
def communication() -> CommunicationProtocol:
    return CommunicationProtocol()


@pytest.fixture
def handoff_manager(
    registry: AgentRegistry,
    communication: CommunicationProtocol,
    event_bus: EventBus,
) -> HandoffManager:
    return HandoffManager(
        registry=registry,
        communication=communication,
        event_bus=event_bus,
    )


class TestAgentHierarchy:
    """Tests for the agent hierarchy."""

    def test_build_hierarchy(self, hierarchy: AgentHierarchy) -> None:
        """CEO should have 7 directors."""
        directors = hierarchy.get_subordinates(AgentType.CEO)
        assert len(directors) == 7
        assert AgentType.MARKETING_DIRECTOR in directors
        assert AgentType.COMPLIANCE_DIRECTOR in directors

    def test_director_subordinates(self, hierarchy: AgentHierarchy) -> None:
        """Marketing Director should have 3 specialists."""
        subs = hierarchy.get_subordinates(AgentType.MARKETING_DIRECTOR)
        assert len(subs) == 3
        assert AgentType.CONTENT_SPECIALIST in subs
        assert AgentType.SEO_SPECIALIST in subs
        assert AgentType.SOCIAL_SPECIALIST in subs

    def test_get_supervisor(self, hierarchy: AgentHierarchy) -> None:
        """Content Specialist's supervisor should be Marketing Director."""
        supervisor = hierarchy.get_supervisor(AgentType.CONTENT_SPECIALIST)
        assert supervisor == AgentType.MARKETING_DIRECTOR

    def test_ceo_has_no_supervisor(self, hierarchy: AgentHierarchy) -> None:
        supervisor = hierarchy.get_supervisor(AgentType.CEO)
        assert supervisor is None

    def test_get_path_to_root(self, hierarchy: AgentHierarchy) -> None:
        """Path from Content Specialist to CEO."""
        path = hierarchy.get_path_to_root(AgentType.CONTENT_SPECIALIST)
        assert path[0] == AgentType.CONTENT_SPECIALIST
        assert path[1] == AgentType.MARKETING_DIRECTOR
        assert path[2] == AgentType.CEO
        assert len(path) == 3

    def test_ceo_path_is_self(self, hierarchy: AgentHierarchy) -> None:
        path = hierarchy.get_path_to_root(AgentType.CEO)
        assert path == [AgentType.CEO]

    def test_can_delegate_to_subordinate(self, hierarchy: AgentHierarchy) -> None:
        assert hierarchy.can_delegate(AgentType.CEO, AgentType.MARKETING_DIRECTOR) is True

    def test_can_delegate_ceo_anyone(self, hierarchy: AgentHierarchy) -> None:
        assert hierarchy.can_delegate(AgentType.CEO, AgentType.CONTENT_SPECIALIST) is True

    def test_cannot_delegate_up(self, hierarchy: AgentHierarchy) -> None:
        assert hierarchy.can_delegate(AgentType.MARKETING_DIRECTOR, AgentType.CEO) is False

    def test_cannot_delegate_sideways(self, hierarchy: AgentHierarchy) -> None:
        assert (
            hierarchy.can_delegate(AgentType.MARKETING_DIRECTOR, AgentType.CREATIVE_DIRECTOR)
            is False
        )

    def test_leaf_agents_have_no_subordinates(self, hierarchy: AgentHierarchy) -> None:
        leaf_types = [
            AgentType.CONTENT_SPECIALIST,
            AgentType.SEO_SPECIALIST,
            AgentType.COPYWRITER,
            AgentType.DATA_ANALYST,
        ]
        for leaf in leaf_types:
            subs = hierarchy.get_subordinates(leaf)
            assert subs == [], f"{leaf} should have no subordinates"


class TestCommunicationProtocol:
    """Tests for inter-agent messaging."""

    @pytest.mark.asyncio
    async def test_send_and_receive(self, communication: CommunicationProtocol) -> None:
        from services.agent_orchestrator.agent import AgentMessage

        sender = uuid.uuid4()
        receiver = uuid.uuid4()
        msg = AgentMessage(
            from_agent=sender,
            to_agent=receiver,
            message_type="request",
            payload={"task": "do something"},
        )
        sent = await communication.send_message(msg)
        assert sent is True

        received = await communication.receive_message(receiver, timeout=1.0)
        assert received is not None
        assert received.from_agent == sender
        assert received.message_type == "request"

    @pytest.mark.asyncio
    async def test_receive_timeout(self, communication: CommunicationProtocol) -> None:
        result = await communication.receive_message(uuid.uuid4(), timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_broadcast(self, communication: CommunicationProtocol) -> None:
        from services.agent_orchestrator.agent import AgentMessage

        sender = uuid.uuid4()
        receivers = [uuid.uuid4() for _ in range(3)]
        msg = AgentMessage(
            from_agent=sender,
            to_agent=receivers[0],
            message_type="notification",
            payload={"info": "broadcast"},
        )
        sent = await communication.broadcast(msg, receivers)
        assert sent == 3

    def test_subscribe_unsubscribe(self, communication: CommunicationProtocol) -> None:
        agent_id = uuid.uuid4()
        communication.subscribe(agent_id, "marketing")
        assert "marketing" in communication._subscriptions[agent_id]
        communication.unsubscribe(agent_id, "marketing")
        assert "marketing" not in communication._subscriptions.get(agent_id, set())


class TestHandoffManager:
    """Tests for handoff management."""

    @pytest.mark.asyncio
    async def test_handle_handoff_request_accept(
        self, handoff_manager: HandoffManager
    ) -> None:

        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.CONTENT_SPECIALIST, uuid.uuid4())
        agent.config.capabilities = ["content_creation"]

        msg = AgentMessage(
            from_agent=uuid.uuid4(),
            to_agent=agent.agent_id,
            message_type="handoff_request",
            payload={"required_capabilities": ["content_creation"]},
        )
        response = await handoff_manager.handle_handoff_request(agent, msg)
        assert response.accepted is True

    @pytest.mark.asyncio
    async def test_handle_handoff_request_reject(
        self, handoff_manager: HandoffManager
    ) -> None:

        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.CONTENT_SPECIALIST, uuid.uuid4())

        msg = AgentMessage(
            from_agent=uuid.uuid4(),
            to_agent=agent.agent_id,
            message_type="handoff_request",
            payload={"required_capabilities": ["quantum_computing"]},
        )
        response = await handoff_manager.handle_handoff_request(agent, msg)
        assert response.accepted is False


class TestHandoffRequest:
    """Tests for HandoffRequest dataclass."""

    def test_create_request(self) -> None:
        req = HandoffRequest(
            from_agent=uuid.uuid4(),
            to_agent=uuid.uuid4(),
            handoff_type=HandoffType.DELEGATION,
            task_description="Create blog post",
            context={"priority": "high"},
            required_capabilities=["content_creation"],
        )
        assert req.handoff_type == HandoffType.DELEGATION
        assert "content_creation" in req.required_capabilities

    def test_request_types(self) -> None:
        assert HandoffType.DELEGATION.value == "delegation"
        assert HandoffType.ESCALATION.value == "escalation"
        assert HandoffType.PEER.value == "peer"
        assert HandoffType.SPECIALIST.value == "specialist"
