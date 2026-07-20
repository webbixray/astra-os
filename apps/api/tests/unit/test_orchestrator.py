from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.agents.orchestrator import PRESET_AGENTS, AgentOrchestrator
from app.domain.entities.agents.agent import Agent, AgentRole, AgentStatus
from app.domain.entities.agents.task import AgentTask


@pytest.fixture
def orchestrator():
    mock_registry = MagicMock()
    mock_bus = MagicMock()
    orch = AgentOrchestrator.__new__(AgentOrchestrator)
    orch.tool_registry = mock_registry
    orch.message_bus = mock_bus
    orch.agents = {}
    orch.tasks = {}
    return orch


def make_agent(name: str, role: AgentRole = AgentRole.CAMPAIGN_DIRECTOR):
    agent = MagicMock(spec=Agent)
    agent.name = name
    agent.id = uuid4()
    agent.role = role
    agent.set_status = MagicMock()
    return agent


def make_task(title: str = "Test task", description: str = "Test description"):
    task = MagicMock(spec=AgentTask)
    task.id = uuid4()
    task.title = title
    task.description = description
    task.assigned_by = uuid4()
    task.complete = MagicMock()
    task.fail = MagicMock()
    task.assign = MagicMock()
    task.start = MagicMock()
    return task


class TestPresetAgents:
    def test_preset_agents_defined(self):
        assert len(PRESET_AGENTS) == 5

    def test_preset_contains_ceo(self):
        names = [a["name"] for a in PRESET_AGENTS]
        assert "ASTRA-CEO" in names


class TestInit:
    def test_init_with_defaults(self):
        with patch(
            "app.application.use_cases.agents.orchestrator.AgentOrchestrator._init_preset_agents",
            MagicMock(),
        ):
            with patch("app.application.use_cases.agents.orchestrator.ToolRegistry") as MockToolReg:
                with patch("app.application.use_cases.agents.orchestrator.MessageBus") as MockBus:
                    MockToolReg.return_value = MagicMock()
                    MockBus.return_value = MagicMock()
                    orch = AgentOrchestrator()
                    assert orch.tool_registry is not None
                    assert orch.message_bus is not None

    def test_init_preset_agents(self, orchestrator):
        orchestrator._init_preset_agents()

        assert len(orchestrator.agents) == 5
        assert "ASTRA-CEO" in orchestrator.agents
        assert "Campaign Director" in orchestrator.agents
        assert "Content Director" in orchestrator.agents
        assert "Analytics Director" in orchestrator.agents
        assert "Workflow Director" in orchestrator.agents


class TestGetCEO:
    def test_get_ceo(self, orchestrator):
        ceo = MagicMock(spec=Agent)
        ceo.name = "ASTRA-CEO"
        orchestrator.agents["ASTRA-CEO"] = ceo

        result = orchestrator.get_ceo()

        assert result == ceo


class TestGetDirectorForTask:
    @pytest.mark.asyncio
    async def test_campaign_task(self, orchestrator):
        orchestrator.agents["Campaign Director"] = make_agent("Campaign Director")
        task = make_task(title="Campaign budget review", description="Need help with campaigns")

        result = await orchestrator.get_director_for_task(task)

        assert result.name == "Campaign Director"

    @pytest.mark.asyncio
    async def test_content_task(self, orchestrator):
        orchestrator.agents["Content Director"] = make_agent("Content Director")
        task = make_task(title="Blog post", description="Write a blog")

        result = await orchestrator.get_director_for_task(task)

        assert result.name == "Content Director"

    @pytest.mark.asyncio
    async def test_analytics_task(self, orchestrator):
        orchestrator.agents["Analytics Director"] = make_agent("Analytics Director")
        task = make_task(title="Monthly report", description="Analyze metrics")

        result = await orchestrator.get_director_for_task(task)

        assert result.name == "Analytics Director"

    @pytest.mark.asyncio
    async def test_workflow_task(self, orchestrator):
        orchestrator.agents["Workflow Director"] = make_agent("Workflow Director")
        task = make_task(title="Approval routing", description="Set up automation")

        result = await orchestrator.get_director_for_task(task)

        assert result.name == "Workflow Director"

    @pytest.mark.asyncio
    async def test_default_to_campaign(self, orchestrator):
        orchestrator.agents["Campaign Director"] = make_agent("Campaign Director")
        task = make_task(title="General question", description="Hello")

        result = await orchestrator.get_director_for_task(task)

        assert result.name == "Campaign Director"


class TestProcessUserRequest:
    async def test_success(self, orchestrator):
        ceo = MagicMock(spec=Agent)
        ceo.name = "ASTRA-CEO"
        ceo.set_status = MagicMock()
        orchestrator.agents["ASTRA-CEO"] = ceo
        orchestrator.get_ceo = MagicMock(return_value=ceo)
        orchestrator._route_task = AsyncMock(
            return_value={
                "response": "Done",
                "agents_involved": ["Campaign Director"],
            }
        )

        result = await orchestrator.process_user_request(uuid4(), uuid4(), "Create campaign")

        assert result["status"] == "completed"
        assert result["response"] == "Done"
        ceo.set_status.assert_any_call(AgentStatus.PROCESSING)
        ceo.set_status.assert_any_call(AgentStatus.IDLE)

    async def test_error_handling(self, orchestrator):
        ceo = MagicMock(spec=Agent)
        ceo.name = "ASTRA-CEO"
        ceo.set_status = MagicMock()
        orchestrator.agents["ASTRA-CEO"] = ceo
        orchestrator.get_ceo = MagicMock(return_value=ceo)
        orchestrator._route_task = AsyncMock(side_effect=ValueError("DB down"))

        result = await orchestrator.process_user_request(uuid4(), uuid4(), "Create campaign")

        assert result["status"] == "failed"
        assert "error" in result["response"].lower()
        ceo.set_status.assert_any_call(AgentStatus.ERROR)


class TestRouteTask:
    async def test_route_to_campaign_director(self, orchestrator):
        director = MagicMock(spec=Agent)
        director.name = "Campaign Director"
        director.id = uuid4()
        director.set_status = MagicMock()
        orchestrator.get_director_for_task = AsyncMock(return_value=director)
        orchestrator._decompose_task = MagicMock(return_value=[])
        orchestrator._execute_subtask = AsyncMock(side_effect=[])

        task = make_task(title="Campaign task", description="Create a campaign")
        result = await orchestrator._route_task(task, uuid4())

        assert "agents_involved" in result

    async def test_route_executes_subtasks(self, orchestrator):
        director = MagicMock(spec=Agent)
        director.name = "Campaign Director"
        director.id = uuid4()
        director.set_status = MagicMock()
        orchestrator.get_director_for_task = AsyncMock(return_value=director)
        orchestrator._decompose_task = MagicMock(
            return_value=[
                make_task(title="Subtask 1"),
                make_task(title="Subtask 2"),
            ]
        )
        orchestrator._execute_subtask = AsyncMock(
            side_effect=[
                {"tool": "tool1", "result": "done1"},
                {"tool": "tool2", "result": "done2"},
            ]
        )

        result = await orchestrator._route_task(task=make_task(), organization_id=uuid4())

        assert result["response"] == "done1\n\ndone2"
        assert director.set_status.call_count == 2
        assert len(result["subtask_results"]) == 2


class TestDecomposeTask:
    def test_campaign_director_create(self, orchestrator):
        task = make_task(title="Create campaign", description="Please create a new campaign")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Campaign Director")

        assert len(subtasks) == 1
        assert "Generate campaign suggestions" in subtasks[0].title

    def test_campaign_director_optimize(self, orchestrator):
        task = make_task(title="Optimize campaign", description="Improve performance")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Campaign Director")

        assert len(subtasks) >= 1
        titles = [t.title for t in subtasks]
        assert "Analyze campaign performance" in titles

    def test_campaign_director_create_and_optimize(self, orchestrator):
        task = make_task(
            title="Create and optimize", description="Create new campaign and improve existing"
        )
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Campaign Director")

        assert len(subtasks) == 2

    def test_content_director_create(self, orchestrator):
        task = make_task(title="Write blog", description="Write a blog post about AI")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Content Director")

        assert len(subtasks) == 1
        assert "Generate content outline" in subtasks[0].title

    def test_content_director_review(self, orchestrator):
        task = make_task(title="Review content", description="Review and provide feedback")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Content Director")

        assert len(subtasks) == 1
        assert "Review content quality" in subtasks[0].title

    def test_content_director_create_and_review(self, orchestrator):
        task = make_task(title="Write and review", description="Write and review content")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Content Director")

        assert len(subtasks) == 2

    def test_analytics_director(self, orchestrator):
        task = make_task(title="Analytics report", description="Generate analytics report")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Analytics Director")

        assert len(subtasks) == 1
        assert "Gather performance data" in subtasks[0].title

    def test_workflow_director_fallback(self, orchestrator):
        task = make_task(title="General request", description="Something unrelated")
        task.assigned_by = uuid4()

        subtasks = orchestrator._decompose_task(task, "Workflow Director")

        assert len(subtasks) == 1
        assert "Process request" in subtasks[0].title


class TestExecuteSubtask:
    async def test_matching_tool_succeeds(self, orchestrator):
        tool = MagicMock()
        tool.name = "create_campaign"
        tool.execute = AsyncMock(return_value={"response": "Campaign created"})
        orchestrator.tool_registry.list_by_category = MagicMock(return_value=[tool])

        subtask = make_task(
            title="Create campaign suggestions", description="Create a new campaign"
        )
        result = await orchestrator._execute_subtask(subtask, MagicMock(), uuid4())

        assert result["tool"] == "create_campaign"
        assert result["result"]["response"] == "Campaign created"
        subtask.complete.assert_called()

    async def test_matching_tool_fails(self, orchestrator):
        tool = MagicMock()
        tool.name = "create_campaign"
        tool.execute = AsyncMock(side_effect=ValueError("API error"))
        orchestrator.tool_registry.list_by_category = MagicMock(return_value=[tool])

        subtask = make_task(
            title="Create campaign suggestions", description="Create a new campaign"
        )
        result = await orchestrator._execute_subtask(subtask, MagicMock(), uuid4())

        assert result["tool"] == "create_campaign"
        assert "error" in result
        subtask.fail.assert_called()

    async def test_no_matching_tool(self, orchestrator):
        tool = MagicMock()
        tool.name = "unrelated_tool"
        tool.execute = AsyncMock()
        orchestrator.tool_registry.list_by_category = MagicMock(return_value=[tool])

        subtask = make_task(title="Create campaign", description="Create a campaign")
        result = await orchestrator._execute_subtask(subtask, MagicMock(), uuid4())

        assert result["tool"] == "default"
        assert "noted" in result["result"].lower()
        subtask.start.assert_called()

    async def test_multiple_tools_matches_first(self, orchestrator):
        tool1 = MagicMock()
        tool1.name = "create_campaign"
        tool1.execute = AsyncMock(return_value={"response": "First tool"})
        tool2 = MagicMock()
        tool2.name = "create_campaign_v2"
        tool2.execute = AsyncMock(return_value={"response": "Second tool"})
        orchestrator.tool_registry.list_by_category = MagicMock(return_value=[tool1, tool2])

        subtask = make_task(title="Create campaign", description="Create")
        result = await orchestrator._execute_subtask(subtask, MagicMock(), uuid4())

        assert result["result"]["response"] == "First tool"


class TestConsolidateResults:
    def test_result_with_response(self, orchestrator):
        results = [{"result": {"response": "Campaign created"}}]

        consolidated = orchestrator._consolidate_results(results)

        assert consolidated == "Campaign created"

    def test_result_with_error_in_result(self, orchestrator):
        results = [{"result": {"error": "Budget exceeded"}}]

        consolidated = orchestrator._consolidate_results(results)

        assert "Issue: Budget exceeded" in consolidated

    def test_result_with_direct_string(self, orchestrator):
        results = [{"result": "Direct string result"}]

        consolidated = orchestrator._consolidate_results(results)
        assert consolidated == "Direct string result"

    def test_result_with_direct_dict(self, orchestrator):
        results = [{"result": {"key": "value"}}]

        consolidated = orchestrator._consolidate_results(results)

        assert "{'key': 'value'}" in consolidated

    def test_result_with_error(self, orchestrator):
        results = [{"error": "Something failed"}]

        consolidated = orchestrator._consolidate_results(results)

        assert "Note: Something failed" in consolidated

    def test_empty_results(self, orchestrator):
        consolidated = orchestrator._consolidate_results([])

        assert "processed" in consolidated

    def test_multiple_results(self, orchestrator):
        results = [
            {"result": {"response": "First"}},
            {"result": {"response": "Second"}},
        ]

        consolidated = orchestrator._consolidate_results(results)

        assert consolidated == "First\n\nSecond"
