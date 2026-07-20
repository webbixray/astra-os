"""Tests for the tool registry and execution sandbox."""

import asyncio

import pytest

from astra_agent_orchestrator.tools import (
    ExecutionSandbox,
    ToolRegistry,
)

from .conftest import MockTool


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        assert "test_tool" in registry.tools

    def test_unregister_tool(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        assert registry.unregister("test_tool") is True
        assert "test_tool" not in registry.tools

    def test_unregister_nonexistent(self) -> None:
        registry = ToolRegistry()
        assert registry.unregister("nonexistent") is False

    def test_get_tool(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        assert registry.get_tool("test_tool") is tool
        assert registry.get_tool("nonexistent") is None

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        registry.register(tool1)
        registry.register(tool2)
        definitions = registry.list_tools()
        assert len(definitions) == 2
        names = {d.name for d in definitions}
        assert names == {"tool1", "tool2"}

    def test_list_categories(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        assert "general" in registry.list_categories()

    def test_get_tools_by_category(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        tools = registry.get_tools_by_category("general")
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_get_tool_openai_functions(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        functions = registry.get_tool_openai_functions()
        assert len(functions) == 1
        assert functions[0]["type"] == "function"
        assert functions[0]["function"]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool", return_value="hello")
        registry.register(tool)
        result = await registry.execute_tool("test_tool", {"query": "test"})
        assert result["success"] is True
        assert result["result"] == "hello"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self) -> None:
        registry = ToolRegistry()
        result = await registry.execute_tool("nonexistent", {})
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_tool_validation_error(self) -> None:
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        # Missing required 'query' parameter
        result = await registry.execute_tool("test_tool", {})
        assert result["success"] is False
        assert "Required parameter" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self) -> None:
        registry = ToolRegistry()

        class SlowTool(MockTool):
            async def execute(self, **kwargs: object) -> str:
                await asyncio.sleep(10)
                return "slow"

        tool = SlowTool(name="slow_tool")
        tool.definition.timeout_seconds = 1
        registry.register(tool)
        result = await registry.execute_tool("slow_tool", {"query": "test"})
        assert result["success"] is False
        assert "timed out" in result["error"]


class TestToolParameterValidation:
    """Tests for tool parameter validation."""

    def test_validate_params_success(self) -> None:
        tool = MockTool(name="test")
        valid, error = tool.validate_params({"query": "hello"})
        assert valid is True
        assert error is None

    def test_validate_params_missing_required(self) -> None:
        tool = MockTool(name="test")
        valid, error = tool.validate_params({})
        assert valid is False
        assert "Required parameter" in error

    def test_validate_params_wrong_type(self) -> None:
        tool = MockTool(name="test")
        valid, error = tool.validate_params({"query": 123})
        assert valid is False
        assert "invalid type" in error


class TestExecutionSandbox:
    """Tests for the execution sandbox."""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5)
        result = await sandbox.execute_python("x = 1 + 2")
        assert result["success"] is True
        assert result["result"]["x"] == 3

    @pytest.mark.asyncio
    async def test_execute_blocked_import(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5)
        result = await sandbox.execute_python("import os")
        assert result["success"] is False
        assert "not allowed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_dangerous_pattern(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5)
        result = await sandbox.execute_python("eval('1+1')")
        assert result["success"] is False
        assert "Dangerous pattern" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_timeout(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=1)
        result = await sandbox.execute_python("import time; time.sleep(10)")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_safe_import(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5)
        result = await sandbox.execute_python("x = json.dumps([1, 2, 3])")
        assert result["success"] is True
        assert result["result"]["x"] == "[1, 2, 3]"

    @pytest.mark.asyncio
    async def test_execute_command_not_allowed(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5, allow_filesystem=True)
        result = await sandbox.execute_command(["rm", "-rf", "/"])
        assert result["success"] is False
        assert "not allowed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_command_no_filesystem(self) -> None:
        sandbox = ExecutionSandbox(timeout_seconds=5, allow_filesystem=False)
        result = await sandbox.execute_command(["ls"])
        assert result["success"] is False
        assert "Filesystem access not allowed" in result["error"]

    def test_validate_code_safe(self) -> None:
        sandbox = ExecutionSandbox()
        valid, error = sandbox.validate_code("x = 1 + 2")
        assert valid is True

    def test_validate_code_blocked_module(self) -> None:
        sandbox = ExecutionSandbox()
        valid, error = sandbox.validate_code("import subprocess")
        assert valid is False
        assert "not allowed" in error
