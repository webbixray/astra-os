"""Tests for agent registry and agent creation."""

import uuid

import pytest

from services.agent_orchestrator.agent import (
    AgentConfig,
    AgentContext,
    AgentRegistry,
    AgentResult,
    AgentState,
    AgentType,
)
from services.agent_orchestrator.agents.ceo import CEOAgent
from services.agent_orchestrator.agents.director import DirectorAgent
from services.agent_orchestrator.agents.specialist import SpecialistAgent


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_config(self) -> None:
        config = AgentConfig()
        assert config.agent_type == AgentType.CEO
        assert config.autonomy_level == 0
        assert config.max_iterations == 10
        assert config.tenant_id is None

    def test_custom_config(self) -> None:
        config = AgentConfig(
            agent_type=AgentType.MARKETING_DIRECTOR,
            name="Test Director",
            capabilities=["planning"],
            autonomy_level=1,
        )
        assert config.agent_type == AgentType.MARKETING_DIRECTOR
        assert config.name == "Test Director"
        assert "planning" in config.capabilities


class TestAgentContext:
    """Tests for AgentContext."""

    def test_create_context(self) -> None:
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        ctx = AgentContext(
            agent_id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        assert ctx.tenant_id == tenant_id
        assert ctx.user_id == user_id
        assert ctx.session_id is not None
        assert ctx.trace_id is not None

    def test_child_context(self) -> None:
        parent = AgentContext(
            agent_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        child = parent.child_context(uuid.uuid4())
        assert child.tenant_id == parent.tenant_id
        assert child.user_id == parent.user_id
        assert child.session_id == parent.session_id
        assert child.parent_context is parent


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_create_agent_types_registered(self, registry: AgentRegistry) -> None:
        """Verify default agent types are registered."""
        types = registry.list_agent_types()
        assert AgentType.CEO in types
        assert AgentType.MARKETING_DIRECTOR in types
        assert AgentType.CREATIVE_DIRECTOR in types

    def test_create_ceo_agent(self, registry: AgentRegistry, tenant_id: uuid.UUID) -> None:
        """CEO agent should be created as CEOAgent instance."""
        agent = registry.create_agent(AgentType.CEO, tenant_id)
        assert isinstance(agent, CEOAgent)
        assert agent.agent_type == AgentType.CEO
        assert agent.tenant_id == tenant_id

    def test_create_director_agent(self, registry: AgentRegistry, tenant_id: uuid.UUID) -> None:
        """Director agents should be created as DirectorAgent instances."""
        agent = registry.create_agent(AgentType.MARKETING_DIRECTOR, tenant_id)
        assert isinstance(agent, DirectorAgent)
        assert agent.agent_type == AgentType.MARKETING_DIRECTOR

    def test_create_specialist_agent(self, registry: AgentRegistry, tenant_id: uuid.UUID) -> None:
        """Specialist agents should be created as SpecialistAgent instances."""
        agent = registry.create_agent(AgentType.CONTENT_SPECIALIST, tenant_id)
        assert isinstance(agent, SpecialistAgent)
        assert agent.agent_type == AgentType.CONTENT_SPECIALIST

    def test_create_any_agent_type(self, registry: AgentRegistry) -> None:
        """Any valid AgentType should be creatable via auto-registration."""
        agent = registry.create_agent(AgentType.KNOWLEDGE_GRAPH_OPERATOR, uuid.uuid4())
        assert agent.agent_type == AgentType.KNOWLEDGE_GRAPH_OPERATOR
        assert agent.agent_id is not None

    def test_get_agent(self, registry: AgentRegistry, tenant_id: uuid.UUID) -> None:
        agent = registry.create_agent(AgentType.CEO, tenant_id)
        found = registry.get_agent(agent.agent_id)
        assert found is agent

    def test_get_config(self, registry: AgentRegistry) -> None:
        config = registry.get_config(AgentType.CEO)
        assert config is not None
        assert config.agent_type == AgentType.CEO

    def test_register_custom_agent_type(
        self, registry: AgentRegistry, tenant_id: uuid.UUID
    ) -> None:
        config = AgentConfig(
            agent_type=AgentType.KNOWLEDGE_GRAPH_OPERATOR,
            name="KG Operator",
            capabilities=["graph"],
        )
        registry.register_agent_type(AgentType.KNOWLEDGE_GRAPH_OPERATOR, config)
        agent = registry.create_agent(AgentType.KNOWLEDGE_GRAPH_OPERATOR, tenant_id)
        assert agent.config.name == "KG Operator"

    def test_config_overrides(self, registry: AgentRegistry, tenant_id: uuid.UUID) -> None:
        agent = registry.create_agent(
            AgentType.CEO,
            tenant_id,
            config_overrides={"name": "Custom CEO", "temperature": 0.3},
        )
        assert agent.config.name == "Custom CEO"
        assert agent.config.temperature == 0.3


class TestAgentType:
    """Tests for AgentType enum."""

    def test_all_director_types(self) -> None:
        directors = {
            AgentType.MARKETING_DIRECTOR,
            AgentType.CREATIVE_DIRECTOR,
            AgentType.ADVERTISING_DIRECTOR,
            AgentType.RESEARCH_DIRECTOR,
            AgentType.ANALYTICS_DIRECTOR,
            AgentType.WORKFLOW_DIRECTOR,
            AgentType.COMPLIANCE_DIRECTOR,
        }
        assert len(directors) == 7

    def test_agent_type_values(self) -> None:
        assert AgentType.CEO.value == "CEO"
        assert AgentType.CONTENT_SPECIALIST.value == "CONTENT_SPECIALIST"
