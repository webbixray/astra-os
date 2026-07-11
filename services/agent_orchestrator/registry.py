"""Agent Registry for managing agent instances."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

from .agent import AgentConfig, AgentState, BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for managing agent definitions and instances."""

    def __init__(self):
        self._definitions: dict[str, type[BaseAgent]] = {}
        self._instances: dict[UUID, BaseAgent] = {}
        self._configs: dict[UUID, AgentConfig] = {}
        self._health_checks: dict[str, Callable[[], bool]] = {}
        _instance_lock: asyncio.Lock = asyncio.Lock()

    def register_agent_type(
        self,
        agent_type: str,
        agent_class: type[BaseAgent],
        health_check: Callable[[], bool] | None = None,
    ) -> None:
        """Register an agent type."""
        if agent_type in self._definitions:
            logger.warning("Overwriting existing agent type: %s", agent_type)
        self._definitions[agent_type] = agent_class
        if health_check:
            self._health_checks[agent_type] = health_check
        logger.info("Registered agent type: %s", agent_type)

    def unregister_agent_type(self, agent_type: str) -> None:
        """Unregister an agent type."""
        self._definitions.pop(agent_type, None)
        self._health_checks.pop(agent_type, None)
        logger.info("Unregistered agent type: %s", agent_type)

    def get_agent_type(self, agent_type: str) -> type[BaseAgent] | None:
        """Get agent class by type."""
        return self._definitions.get(agent_type)

    def list_agent_types(self) -> list[str]:
        """List all registered agent types."""
        return list(self._definitions.keys())

    async def create_agent(
        self,
        agent_type: str,
        config: AgentConfig,
        context: "AgentContext",
        tool_registry: "ToolRegistry",
        memory_manager: "MemoryManager | None" = None,
        event_bus: "EventBus | None" = None,
    ) -> BaseAgent:
        """Create and register a new agent instance."""
        agent_class = self._definitions.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        async with _instance_lock:
            agent = agent_class(
                config=config,
                context=context,
                tool_registry=tool_registry,
                memory_manager=memory_manager,
                event_bus=event_bus,
            )
            await agent.initialize()

            self._instances[config.agent_id] = agent
            self._configs[config.agent_id] = config

        logger.info("Created agent instance: %s (%s)", config.agent_id, agent_type)
        return agent

    def get_agent(self, agent_id: UUID) -> BaseAgent | None:
        """Get an agent instance by ID."""
        return self._instances.get(agent_id)

    def get_agent_state(self, agent_id: UUID) -> AgentState | None:
        """Get agent state by ID."""
        agent = self._instances.get(agent_id)
        return agent.get_state() if agent else None

    def get_agent_config(self, agent_id: UUID) -> AgentConfig | None:
        """Get agent config by ID."""
        return self._configs.get(agent_id)

    async def remove_agent(self, agent_id: UUID) -> bool:
        """Remove and cleanup an agent instance."""
        async with _instance_lock:
            agent = self._instances.pop(agent_id, None)
            self._configs.pop(agent_id, None)

        if agent:
            agent.cancel()
            await agent._cleanup()
            logger.info("Removed agent: %s", agent_id)
            return True
        return False

    async def health_check(self, agent_type: str | None = None) -> dict[str, Any]:
        """Run health checks on agent types."""
        results = {}

        types_to_check = [agent_type] if agent_type else list(self._definitions.keys())

        for atype in types_to_check:
            if atype in self._health_checks:
                try:
                    healthy = self._health_checks[atype]()
                    results[atype] = {"healthy": healthy}
                except Exception as e:
                    results[atype] = {"healthy": False, "error": str(e)}
            else:
                results[atype] = {"healthy": True, "note": "No health check defined"}

        return results

    def list_agents(self, agent_type: str | None = None) -> list[dict[str, Any]]:
        """List all agent instances."""
        agents = []
        for agent_id, agent in self._instances.items():
            if agent_type is None or agent.agent_type == agent_type:
                agents.append(
                    {
                        "agent_id": str(agent_id),
                        "agent_type": agent.agent_type,
                        "name": agent.config.name,
                        "status": agent.state.status.value,
                        "current_task": agent.state.current_task,
                        "iteration": agent.state.iteration,
                    }
                )
        return agents

    async def shutdown(self) -> None:
        """Shutdown all agents."""
        async with _instance_lock:
            agent_ids = list(self._instances.keys())

        for agent_id in agent_ids:
            await self.remove_agent(agent_id)

        logger.info("Agent registry shutdown complete")


# Global registry instance
agent_registry = AgentRegistry()