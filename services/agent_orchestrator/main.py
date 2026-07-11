"""
Agent Orchestrator Runtime - Main Entry Point.

This module provides the main entry point for running the Agent Orchestrator service.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from pydantic_settings import BaseSettings

from services.agent_orchestrator.agent import Agent, AgentConfig, AgentType
from services.agent_orchestrator.events import get_event_bus
from services.agent_orchestrator.memory import MemoryManager
from services.agent_orchestrator.tools import default_sandbox, tool_registry

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://astra:astra_dev@localhost:5432/astra"
    database_pool_size: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Agent Runtime
    agent_pool_size: int = 10
    default_agent_timeout: int = 300

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


class AgentOrchestrator:
    """Main orchestrator service."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.pg_pool: asyncpg.Pool | None = None
        self.redis_client: redis.Redis | None = None
        self.memory_manager: MemoryManager | None = None
        self._shutdown = False

    async def initialize(self) -> None:
        """Initialize all connections and services."""
        logger.info("Initializing Agent Orchestrator...")

        # PostgreSQL pool
        self.pg_pool = await asyncpg.create_pool(
            self.settings.database_url,
            min_size=5,
            max_size=self.settings.database_pool_size,
        )
        logger.info("PostgreSQL pool created")

        # Redis client
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Redis connected")

        # Memory manager
        self.memory_manager = MemoryManager(
            pg_pool=self.pg_pool,
            redis_client=self.redis_client,
        )

        # Initialize default tools
        await self._register_default_tools()

        # Register signal handlers
        self._setup_signal_handlers()

        logger.info("Agent Orchestrator initialized successfully")

    async def _register_default_tools(self) -> None:
        """Register built-in tools."""
        from services.agent_orchestrator.tools import (
            Tool,
            ToolDefinition,
            ToolParameter,
        )

        # Web search tool
        class WebSearchTool(Tool):
            definition = ToolDefinition(
                name="web_search",
                description="Search the web for information",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Search query",
                        required=True,
                    ),
                    ToolParameter(
                        name="max_results",
                        type="integer",
                        description="Maximum number of results",
                        default=10,
                    ),
                ],
            )

            async def execute(self, query: str, max_results: int = 10, **kwargs) -> dict:
                # In real implementation, would call search API
                return {"results": [{"title": f"Result for {query}", "url": "https://example.com"}]}

        tool_registry.register(WebSearchTool(WebSearchTool.definition))

        # Code execution tool
        class PythonTool(Tool):
            definition = ToolDefinition(
                name="python",
                description="Execute Python code in sandbox",
                parameters=[
                    ToolParameter(
                        name="code",
                        type="string",
                        description="Python code to execute",
                        required=True,
                    ),
                    ToolParameter(
                        name="globals",
                        type="object",
                        description="Global variables to pass to execution",
                    ),
                ],
            )

            async def execute(self, code: str, globals: dict | None = None, **kwargs) -> dict:
                result = await default_sandbox.execute_python(code, globals)
                return result

        tool_registry.register(PythonTool(PythonTool.definition))

        logger.info("Default tools registered")

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()

        def signal_handler(sig, frame):
            logger.info("Received signal %s, initiating shutdown...", sig)
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler, sig, None)

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        if self._shutdown:
            return

        self._shutdown = True
        logger.info("Shutting down Agent Orchestrator...")

        # Close connections
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("PostgreSQL pool closed")

        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

        logger.info("Agent Orchestrator shutdown complete")

    async def run(self) -> None:
        """Run the orchestrator."""
        await self.initialize()

        # Keep running
        while not self._shutdown:
            await asyncio.sleep(1)


async def main() -> None:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    settings = Settings()
    orchestrator = AgentOrchestrator(settings)

    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())