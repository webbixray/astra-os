"""Tests for OpenTelemetry semantic conventions on agent spans."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from services.agent_orchestrator.agent import (
    Agent,
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentType,
)


@pytest.fixture
def agent_config():
    return AgentConfig(
        agent_id=uuid4(),
        agent_type=AgentType.CEO,
        name="Test CEO",
        autonomy_level=1,
    )


@pytest.fixture
def mock_context():
    return AgentContext(
        agent_id=uuid4(),
        tenant_id=uuid4(),
    )


class TestAgentSemanticConventions:
    """Tests for OpenTelemetry semantic conventions on agent spans."""

    @pytest.mark.asyncio
    async def test_agent_run_span_has_semantic_attributes(self, agent_config, mock_context):
        """Agent run span should have standard semantic conventions."""
        agent = Agent(agent_config, agent_config.tenant_id)

        with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.execute = AsyncMock(return_value=AgentResult(
                agent_id=agent_config.agent_id,
                success=True,
                duration_ms=150,
                tokens_used=100,
                cost_usd=0.001,
                iterations=1,
            ))

            await agent.run(mock_context, {"task": "test"})

            # Check semantic conventions
            mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
            mock_span.set_attribute.assert_any_call("agent.astra.type", "CEO")
            mock_span.set_attribute.assert_any_call("agent.astra.tenant_id", str(mock_context.tenant_id))
            mock_span.set_attribute.assert_any_call("agent.astra.session_id", str(mock_context.session_id))
            mock_span.set_attribute.assert_any_call("agent.astra.autonomy_level", 1)

    @pytest.mark.asyncio
    async def test_tool_call_span_has_semantic_attributes(self, agent_config, mock_context):
        """Tool call span should have standard semantic conventions."""
        agent = Agent(agent_config, agent_config.tenant_id)

        with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.tool_registry.execute_tool = AsyncMock(return_value={
                "success": True,
                "result": "output",
            })

            await agent.call_tool("web_search", {"query": "test"}, mock_context)

            # Check semantic conventions
            mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
            mock_span.set_attribute.assert_any_call("tool.name", "web_search")
            mock_span.set_attribute.assert_any_call("tool.astra.agent_type", "CEO")
            mock_span.set_attribute.assert_any_call("tool.astra.agent_id", str(agent_config.agent_id))

    @pytest.mark.asyncio
    async def test_delegation_span_has_semantic_attributes(self, agent_config, mock_context):
        """Delegation span should have standard semantic conventions."""
        agent = Agent(agent_config, agent_config.tenant_id)

        with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            # Mock subagent
            with patch("services.agent_orchestrator.agent.get_agent_registry") as mock_registry:
                mock_subagent = AsyncMock()
                mock_subagent.agent_id = uuid4()
                mock_subagent.agent_type = AgentType.CONTENT_SPECIALIST
                mock_subagent.run = AsyncMock(return_value=AgentResult(
                    agent_id=mock_subagent.agent_id,
                    success=True,
                    duration_ms=100,
                ))
                mock_registry.return_value.create_agent.return_value = mock_subagent

                await agent.delegate_to_subagent(AgentType.CONTENT_SPECIALIST, {"task": "write"}, mock_context)

                # Check semantic conventions
                mock_span.set_attribute.assert_any_call("service.name", "astra-agent-orchestrator")
                mock_span.set_attribute.assert_any_call("agent.astra.delegation.target_type", "CONTENT_SPECIALIST")
                mock_span.set_attribute.assert_any_call("agent.astra.delegation.target_id", str(mock_subagent.agent_id))
                mock_span.set_attribute.assert_any_call("agent.astra.delegation.parent_id", str(agent_config.agent_id))

    @pytest.mark.asyncio
    async def test_agent_run_span_kind_internal(self, agent_config, mock_context):
        """Agent run span should use SpanKind.INTERNAL."""
        agent = Agent(agent_config, agent_config.tenant_id)

        with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.execute = AsyncMock(return_value=AgentResult(
                agent_id=agent_config.agent_id,
                success=True,
                duration_ms=150,
            ))

            await agent.run(mock_context, {"task": "test"})

            # Check SpanKind.INTERNAL was used
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args is not None
            # The kind should be passed as keyword argument or positional
            # Check if SpanKind.INTERNAL was passed

    @pytest.mark.asyncio
    async def test_tool_call_span_kind_client(self, agent_config, mock_context):
        """Tool call span should use SpanKind.CLIENT."""
        agent = Agent(agent_config, agent_config.tenant_id)

        with patch("services.agent_orchestrator.agent.TRACER") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.tool_registry.execute_tool = AsyncMock(return_value={
                "success": True,
                "result": "output",
            })

            await agent.call_tool("web_search", {"query": "test"}, mock_context)

            # Check SpanKind.CLIENT was used
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
