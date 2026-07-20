"""Tests for OpenTelemetry semantic conventions on agent spans."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from opentelemetry.trace import SpanKind
from astra_agent_orchestrator.agent import (
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentType,
)
from astra_agent_orchestrator.agents.ceo import CEOAgent


@pytest.fixture
def tenant_id():
    return uuid4()

@pytest.fixture
def agent_config(tenant_id):
    return AgentConfig(
        agent_id=uuid4(),
        agent_type=AgentType.CEO,
        name="Test CEO",
        autonomy_level=1,
        tenant_id=tenant_id,
    )


@pytest.fixture
def mock_context(tenant_id):
    return AgentContext(
        agent_id=uuid4(),
        tenant_id=tenant_id,
    )


class TestAgentSemanticConventions:
    """Tests for OpenTelemetry semantic conventions on agent spans."""

    @pytest.mark.asyncio
    async def test_agent_run_span_has_semantic_attributes(self, agent_config, mock_context):
        """Agent run span should have standard semantic conventions."""
        agent = CEOAgent(agent_config, agent_config.tenant_id)

        with patch("astra_agent_orchestrator.agent.get_tracer_instance") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer
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

            # Check semantic conventions - they are passed as attributes when starting the span
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args is not None
            attrs = call_args.kwargs.get("attributes", {})
            assert attrs.get("service.name") == "astra-agent-orchestrator"
            assert attrs.get("agent.astra.type") == "CEO"
            assert attrs.get("agent.astra.tenant_id") == str(mock_context.tenant_id)
            assert attrs.get("agent.astra.session_id") == str(mock_context.session_id)
            assert attrs.get("agent.astra.autonomy_level") == 1

    @pytest.mark.asyncio
    async def test_tool_call_span_has_semantic_attributes(self, agent_config, mock_context):
        """Tool call span should have standard semantic conventions."""
        agent = CEOAgent(agent_config, agent_config.tenant_id)

        with patch("astra_agent_orchestrator.agent.get_tracer_instance") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.tool_registry.execute_tool = AsyncMock(return_value={
                "success": True,
                "result": "output",
            })

            await agent.call_tool("web_search", {"query": "test"}, mock_context)

            # Check semantic conventions - they are passed as attributes when starting the span
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args is not None
            attrs = call_args.kwargs.get("attributes", {})
            assert attrs.get("service.name") == "astra-agent-orchestrator"
            assert attrs.get("tool.name") == "web_search"
            assert attrs.get("agent.id") == str(agent_config.agent_id)
            assert attrs.get("agent.type") == "CEO"

    @pytest.mark.asyncio
    async def test_delegation_span_has_semantic_attributes(self, agent_config, mock_context):
        """Delegation span should have standard semantic conventions."""
        agent = CEOAgent(agent_config, agent_config.tenant_id)

        with patch("astra_agent_orchestrator.agent.get_tracer_instance") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            # Mock subagent
            with patch("astra_agent_orchestrator.agent.get_agent_registry") as mock_registry:
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

                # Check semantic conventions - they are passed as attributes when starting the span
                call_args = mock_tracer.start_as_current_span.call_args
                assert call_args is not None
                attrs = call_args.kwargs.get("attributes", {})
                assert attrs.get("service.name") == "astra-agent-orchestrator"
                assert attrs.get("subagent.type") == "CONTENT_SPECIALIST"
                assert attrs.get("subagent.id") == str(mock_subagent.agent_id)
                assert attrs.get("agent.id") == str(agent_config.agent_id)
                assert attrs.get("agent.type") == "CEO"

    @pytest.mark.asyncio
    async def test_agent_run_span_kind_internal(self, agent_config, mock_context):
        """Agent run span should use SpanKind.INTERNAL."""
        agent = CEOAgent(agent_config, agent_config.tenant_id)

        with patch("astra_agent_orchestrator.agent.get_tracer_instance") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            agent.execute = AsyncMock(return_value=AgentResult(
                agent_id=agent_config.agent_id,
                success=True,
                duration_ms=150,
            ))

            await agent.run(mock_context, {"task": "test"})

            # Check span kind is INTERNAL
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args is not None
            # The kind should be passed as keyword argument or positional
            assert call_args.kwargs.get("kind") == SpanKind.INTERNAL or (
                len(call_args.args) > 1 and call_args.args[1] == SpanKind.INTERNAL
            )

    @pytest.mark.asyncio
    async def test_tool_call_span_kind_client(self, agent_config, mock_context):
        """Tool call span should use SpanKind.CLIENT."""
        agent = CEOAgent(agent_config, agent_config.tenant_id)

        with patch("astra_agent_orchestrator.agent.get_tracer_instance") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_get_tracer.return_value = mock_tracer
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
            assert call_args.kwargs.get("kind") == SpanKind.CLIENT or (len(call_args.args) > 1 and call_args.args[1] == SpanKind.CLIENT)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    pytest.main([__file__, "-v"])