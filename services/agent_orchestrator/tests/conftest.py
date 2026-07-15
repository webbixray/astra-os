"""Shared fixtures for agent orchestrator tests."""

import uuid
from typing import Any

import pytest
from services.agent import (
    AgentConfig,
    AgentContext,
    AgentRegistry,
    AgentType,
)
from services.events import EventBus
from services.tools import (
    ExecutionSandbox,
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
)


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def agent_config() -> AgentConfig:
    return AgentConfig(
        agent_type=AgentType.CEO,
        name="Test Agent",
        description="A test agent",
        capabilities=["planning", "testing"],
        autonomy_level=2,
        max_iterations=5,
        temperature=0.7,
    )


@pytest.fixture
def agent_context(tenant_id: uuid.UUID, user_id: uuid.UUID) -> AgentContext:
    return AgentContext(
        agent_id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
    )


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def sandbox() -> ExecutionSandbox:
    return ExecutionSandbox(timeout_seconds=5)


@pytest.fixture
def registry() -> AgentRegistry:
    """Fresh agent registry for testing."""
    return AgentRegistry()


class MockTool(Tool):
    """A simple mock tool for testing."""

    def __init__(self, name: str = "mock_tool", return_value: Any = None):
        super().__init__(
            definition=ToolDefinition(
                name=name,
                description=f"Mock tool: {name}",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Input query",
                        required=True,
                    ),
                ],
            )
        )
        self._return_value = return_value
        self.execute_calls: list[dict] = []

    async def execute(self, query: str = "", **kwargs: Any) -> Any:
        self.execute_calls.append({"query": query, **kwargs})
        return self._return_value or f"Result for: {query}"


@pytest.fixture
def mock_tool() -> MockTool:
    return MockTool()


@pytest.fixture
def tool_registry_with_mock(mock_tool: MockTool) -> ToolRegistry:
    """Tool registry with a mock tool registered."""
    registry = ToolRegistry()
    registry.register(mock_tool)
    return registry
