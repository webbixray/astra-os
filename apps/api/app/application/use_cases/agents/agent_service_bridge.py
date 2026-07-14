"""Bridge adapter connecting API layer to the agent_orchestrator service.

This module provides AgentServiceBridge which wraps the full agent_orchestrator
service (ReAct loop, hierarchy, model router) and exposes it through the API's
existing AgentOrchestrator interface.

Migration path:
  1. Old: API AgentOrchestrator → simple keyword classification → tool handlers
  2. New: API AgentServiceBridge → agent_orchestrator service → ReAct agents

Both coexist during transition. New code should use AgentServiceBridge.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from services.agent_orchestrator.agent import (
    AgentContext,
    AgentType,
    get_agent_registry,
)
from services.agent_orchestrator.agents.ceo import CEOAgent
from services.agent_orchestrator.agents.director import DirectorAgent
from services.agent_orchestrator.comms import get_agent_audit_trail
from services.agent_orchestrator.events import Event, get_event_bus
from services.agent_orchestrator.hierarchy import (
    AgentCoordinator,
    AgentHierarchy,
    CommunicationProtocol,
    HandoffManager,
)
from services.agent_orchestrator.memory import MemoryManager

logger = logging.getLogger(__name__)


class AgentServiceBridge:
    """Bridge between the API layer and the full agent_orchestrator service.

    This replaces the simple keyword-based AgentOrchestrator with the full
    ReAct-based agent hierarchy while maintaining API compatibility.
    """

    def __init__(self) -> None:
        self._registry = get_agent_registry()
        self._hierarchy = AgentHierarchy(self._registry)
        self._communication = CommunicationProtocol()
        self._event_bus = get_event_bus()
        self._handoff_manager = HandoffManager(
            self._registry, self._communication, self._event_bus,
        )
        self._coordinator = AgentCoordinator(
            self._hierarchy, self._communication, self._handoff_manager, self._event_bus,
        )
        self._audit_trail = get_agent_audit_trail()
        self._memory_manager = MemoryManager()

    async def process_user_request(
        self,
        user_id: UUID,
        organization_id: UUID,
        message: str,
    ) -> dict[str, Any]:
        """Process a user request through the full agent hierarchy.

        Flow:
        1. CEO agent decomposes the objective
        2. CEO delegates to appropriate director(s)
        3. Director(s) delegate to specialist(s)
        4. Results are aggregated up the chain
        5. Audit trail is recorded for every step
        """
        tenant_id = organization_id
        context = AgentContext(
            agent_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Publish start event
        await self._event_bus.publish(Event(
            event_type="agent.request.received",
            source="api",
            tenant_id=tenant_id,
            payload={"user_id": str(user_id), "message": message[:200]},
        ))

        try:
            # Create CEO agent
            ceo = CEOAgent(tenant_id=tenant_id)

            # Execute the ReAct loop
            result = await ceo.run(
                context,
                {"objective": message, "context": {"organization_id": str(organization_id)}},
            )

            # Record completion in audit trail
            await self._audit_trail.record_completion(
                agent_id=ceo.agent_id,
                tenant_id=tenant_id,
                agent_type="ceo",
                agent_name="CEO Agent",
                result=result,
            )

            # Publish completion event
            await self._event_bus.publish(Event(
                event_type="agent.request.completed",
                source=str(ceo.agent_id),
                tenant_id=tenant_id,
                payload={
                    "success": result.success,
                    "output": result.output[:500] if result.output else None,
                    "tokens_used": result.tokens_used,
                    "cost_usd": result.cost_usd,
                    "duration_ms": result.duration_ms,
                },
            ))

            return {
                "task_id": str(ceo.agent_id),
                "response": result.output or "No response generated",
                "agents_involved": ["CEO Agent"],
                "status": "completed" if result.success else "failed",
                "metadata": {
                    "tokens_used": result.tokens_used,
                    "cost_usd": result.cost_usd,
                    "duration_ms": result.duration_ms,
                    "iterations": result.iterations,
                },
            }

        except Exception as e:
            logger.exception("Agent service bridge failed")

            await self._event_bus.publish(Event(
                event_type="agent.request.failed",
                source="api",
                tenant_id=tenant_id,
                payload={"error": str(e)},
            ))

            return {
                "task_id": str(uuid4()),
                "response": f"I encountered an error processing your request: {e}",
                "agents_involved": [],
                "status": "failed",
            }

    async def process_with_director(
        self,
        user_id: UUID,
        organization_id: UUID,
        message: str,
        director_type: AgentType,
    ) -> dict[str, Any]:
        """Process a request through a specific director (bypasses CEO).

        Useful when the API already knows which director should handle the task.
        """
        tenant_id = organization_id
        context = AgentContext(
            agent_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )

        try:
            director = DirectorAgent(agent_type=director_type, tenant_id=tenant_id)
            result = await director.run(context, message)

            await self._audit_trail.record_completion(
                agent_id=director.agent_id,
                tenant_id=tenant_id,
                agent_type=director_type.value,
                agent_name=director.config.name,
                result=result,
            )

            return {
                "task_id": str(director.agent_id),
                "response": result.output or "No response generated",
                "agents_involved": [director.config.name],
                "status": "completed" if result.success else "failed",
            }
        except Exception as e:
            logger.exception("Director execution failed")
            return {
                "task_id": str(uuid4()),
                "response": f"Error: {e}",
                "agents_involved": [],
                "status": "failed",
            }

    def get_agents(self) -> list[dict[str, Any]]:
        """Return list of all registered agent types with their configs."""
        agents = []
        for agent_type in self._registry.list_agent_types():
            config = self._registry.get_config(agent_type)
            if config:
                agents.append({
                    "type": agent_type.value,
                    "name": config.name,
                    "description": config.description,
                    "capabilities": config.capabilities,
                    "autonomy_level": config.autonomy_level,
                })
        return agents

    def get_hierarchy(self) -> dict[str, list[str]]:
        """Return the agent hierarchy as a dictionary."""
        return {
            agent_type.value: [sub.value for sub in subs]
            for agent_type, subs in self._hierarchy._hierarchy.items()
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_bridge: AgentServiceBridge | None = None


def get_agent_service_bridge() -> AgentServiceBridge:
    """Get or create the global AgentServiceBridge."""
    global _bridge
    if _bridge is None:
        _bridge = AgentServiceBridge()
    return _bridge
