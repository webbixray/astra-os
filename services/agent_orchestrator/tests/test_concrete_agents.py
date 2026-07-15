"""Tests for concrete agent implementations (CEO, Director, Specialist)."""

import json
import uuid

import pytest
from services.agent import (
    AgentRegistry,
    AgentType,
)
from services.agents import CEOAgent
from services.agents.director import (
    DIRECTOR_CONFIGS,
    DirectorAgent,
)
from services.agents.specialist import (
    SPECIALIST_CONFIGS,
    SpecialistAgent,
)


class TestCEOAgent:
    """Tests for CEO agent."""

    def test_create_ceo(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        assert agent.agent_type == AgentType.CEO
        assert agent.config.autonomy_level == 2

    def test_ceo_system_prompt(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        prompt = agent.get_system_prompt()
        assert "CEO Agent" in prompt
        assert "decompose" in prompt.lower()

    def test_ceo_prepare_input_string(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        result = agent.prepare_input("Launch a new product campaign")
        assert "Launch a new product campaign" in result

    def test_ceo_prepare_input_dict(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        result = agent.prepare_input({
            "objective": "Increase Q4 revenue by 20%",
            "context": {"budget": 50000},
        })
        assert "Increase Q4 revenue" in result
        assert "50000" in result

    def test_ceo_process_output_final_answer(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        output = json.dumps({
            "thought": "I need to decompose this goal",
            "action": None,
            "action_input": None,
            "final_answer": "Campaign plan ready",
        })
        parsed = agent.process_output(output)
        assert parsed["final_answer"] == "Campaign plan ready"
        assert parsed["action"] is None

    def test_ceo_process_output_with_decomposition(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        output = json.dumps({
            "thought": "Decomposing into director tasks",
            "action": None,
            "action_input": None,
            "final_answer": json.dumps({
                "decomposition": {
                    "objective_summary": "Q4 campaign",
                    "tasks": [
                        {"director": "MARKETING_DIRECTOR", "task": "Plan content calendar"}
                    ],
                }
            }),
        })
        parsed = agent.process_output(output)
        assert "decomposition" in parsed

    def test_ceo_process_output_plain_text(self) -> None:
        agent = CEOAgent(tenant_id=uuid.uuid4())
        parsed = agent.process_output("Just a plain text response")
        assert parsed["final_answer"] == "Just a plain text response"

    def test_ceo_prepare_input_from_registry(self) -> None:
        """CEO created from registry should work correctly."""
        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.CEO, uuid.uuid4())
        assert isinstance(agent, CEOAgent)
        result = agent.prepare_input("Test objective")
        assert "Test objective" in result


class TestDirectorAgent:
    """Tests for Director agents."""

    @pytest.mark.parametrize(
        "agent_type",
        [
            AgentType.MARKETING_DIRECTOR,
            AgentType.CREATIVE_DIRECTOR,
            AgentType.ADVERTISING_DIRECTOR,
            AgentType.RESEARCH_DIRECTOR,
            AgentType.ANALYTICS_DIRECTOR,
            AgentType.WORKFLOW_DIRECTOR,
            AgentType.COMPLIANCE_DIRECTOR,
        ],
    )
    def test_create_director(self, agent_type: AgentType) -> None:
        agent = DirectorAgent(agent_type=agent_type, tenant_id=uuid.uuid4())
        assert agent.agent_type == agent_type
        assert agent.config.autonomy_level == 1

    def test_director_subordinates(self) -> None:
        agent = DirectorAgent(
            agent_type=AgentType.MARKETING_DIRECTOR, tenant_id=uuid.uuid4()
        )
        subs = agent.subordinates
        assert AgentType.CONTENT_SPECIALIST in subs
        assert AgentType.SEO_SPECIALIST in subs
        assert AgentType.SOCIAL_SPECIALIST in subs

    def test_director_config_populated(self) -> None:
        for agent_type in DIRECTOR_CONFIGS:
            config = DIRECTOR_CONFIGS[agent_type]
            assert "name" in config
            assert "system_prompt" in config
            assert "subordinates" in config
            assert len(config["subordinates"]) > 0

    def test_director_prepare_input(self) -> None:
        agent = DirectorAgent(
            agent_type=AgentType.MARKETING_DIRECTOR, tenant_id=uuid.uuid4()
        )
        result = agent.prepare_input({
            "task": "Create Q4 content strategy",
            "requirements": ["blog posts", "social media"],
        })
        assert "Q4 content strategy" in result
        assert "CONTENT_SPECIALIST" in result

    def test_director_from_registry(self) -> None:
        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.ADVERTISING_DIRECTOR, uuid.uuid4())
        assert isinstance(agent, DirectorAgent)
        assert len(agent.subordinates) == 3

    def test_all_directors_have_system_prompts(self) -> None:
        for agent_type in DIRECTOR_CONFIGS:
            agent = DirectorAgent(agent_type=agent_type, tenant_id=uuid.uuid4())
            prompt = agent.get_system_prompt()
            assert len(prompt) > 10, f"{agent_type} missing system prompt"


class TestSpecialistAgent:
    """Tests for Specialist agents."""

    @pytest.mark.parametrize(
        "agent_type",
        [
            AgentType.CONTENT_SPECIALIST,
            AgentType.SEO_SPECIALIST,
            AgentType.SOCIAL_SPECIALIST,
            AgentType.COPYWRITER,
            AgentType.DATA_ANALYST,
        ],
    )
    def test_create_specialist(self, agent_type: AgentType) -> None:
        agent = SpecialistAgent(agent_type=agent_type, tenant_id=uuid.uuid4())
        assert agent.agent_type == agent_type
        assert agent.config.autonomy_level == 1

    def test_specialist_config_populated(self) -> None:
        for agent_type in SPECIALIST_CONFIGS:
            config = SPECIALIST_CONFIGS[agent_type]
            assert "name" in config
            assert "system_prompt" in config
            assert "capabilities" in config
            assert len(config["capabilities"]) > 0

    def test_specialist_prepare_input(self) -> None:
        agent = SpecialistAgent(
            agent_type=AgentType.CONTENT_SPECIALIST, tenant_id=uuid.uuid4()
        )
        result = agent.prepare_input({
            "task": "Write a blog post about AI marketing",
            "requirements": ["1500 words", "SEO optimized"],
        })
        assert "AI marketing" in result
        assert "1500 words" in result

    def test_specialist_prepare_input_string(self) -> None:
        agent = SpecialistAgent(
            agent_type=AgentType.SEO_SPECIALIST, tenant_id=uuid.uuid4()
        )
        result = agent.prepare_input("Optimize the landing page")
        assert "Optimize the landing page" in result

    def test_specialist_from_registry(self) -> None:
        registry = AgentRegistry()
        agent = registry.create_agent(AgentType.COPYWRITER, uuid.uuid4())
        assert isinstance(agent, SpecialistAgent)
        assert "copywriting" in agent.config.capabilities

    def test_all_specialists_have_system_prompts(self) -> None:
        for agent_type in SPECIALIST_CONFIGS:
            agent = SpecialistAgent(agent_type=agent_type, tenant_id=uuid.uuid4())
            prompt = agent.get_system_prompt()
            assert len(prompt) > 10, f"{agent_type} missing system prompt"
