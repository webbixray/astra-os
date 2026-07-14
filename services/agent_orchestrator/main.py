"""Agent Orchestrator Runtime - Main Entry Point.

This module provides the main entry point for running the Agent Orchestrator service.
"""

import asyncio
import logging
import os
import signal
import sys
import time

import asyncpg
import redis.asyncio as redis
from pydantic_settings import BaseSettings
from services.agent_orchestrator.dlq import create_dlq_consumer
from services.agent_orchestrator.memory import MemoryManager
from services.agent_orchestrator.supervisor import Supervisor, SupervisorConfig
from services.agent_orchestrator.tools import default_sandbox, tool_registry

logger = logging.getLogger(__name__)

# Monotonic start time for uptime tracking
_START_MONOTONIC = time.monotonic()


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
        self._health_server = None
        self._dlq_consumer = None

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

        # Stop health server
        if self._health_server:
            await self._health_server.shutdown()
            logger.info("Health server stopped")

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

        # Start health check server
        await self._start_health_server()

        # Start DLQ consumer for failed agent tasks
        if self.redis_client:
            try:
                self._dlq_consumer = await create_dlq_consumer(
                    redis_client=self.redis_client,
                    stream="astra:agent:tasks",
                    group_name="agent-orchestrator",
                    consumer_name=f"orchestrator-{int(time.time())}",
                    handler=self._handle_agent_task,
                    max_retries=3,
                    dlq_stream="astra:dlq",
                )
                asyncio.create_task(self._dlq_consumer.run())
                logger.info("DLQ consumer started for agent tasks")
            except Exception as e:
                logger.warning("Failed to start DLQ consumer: %s", e)

        # Keep running
        while not self._shutdown:
            await asyncio.sleep(1)

    async def _handle_agent_task(self, data: dict) -> None:
        """Handle an agent task from the stream."""
        logger.info("Processing agent task: %s", data)
        # In real implementation, would route to appropriate agent

    async def _start_health_server(self) -> None:
        """Start HTTP server for health/liveness probes."""
        try:
            from aiohttp import web
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        except ImportError:
            logger.warning("aiohttp not installed, health endpoint unavailable")
            return

        async def health_live(request):
            """Liveness probe - always returns ok if process is alive."""
            uptime = time.monotonic() - _START_MONOTONIC
            return web.json_response({
                "status": "ok",
                "uptime_seconds": uptime,
                "version": "0.1.0",
            })

        async def health_ready(request):
            """Readiness probe - checks dependencies."""
            checks = {}
            all_healthy = True

            # Check PostgreSQL
            try:
                if self.pg_pool:
                    async with self.pg_pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                    checks["database"] = "ok"
                else:
                    checks["database"] = "not_initialized"
                    all_healthy = False
            except Exception as e:
                checks["database"] = f"error: {e}"
                all_healthy = False

            # Check Redis
            try:
                if self.redis_client:
                    await self.redis_client.ping()
                    checks["redis"] = "ok"
                else:
                    checks["redis"] = "not_initialized"
                    all_healthy = False
            except Exception as e:
                checks["redis"] = f"error: {e}"
                all_healthy = False

            status = 200 if all_healthy else 503
            return web.json_response({
                "ready": all_healthy,
                "checks": checks,
            }, status=status)

        async def metrics_endpoint(request):
            """Prometheus metrics endpoint."""
            return web.Response(
                body=generate_latest(),
                content_type=CONTENT_TYPE_LATEST,
            )

        app = web.Application()
        app.router.add_get("/health/live", health_live)
        app.router.add_get("/health/ready", health_ready)
        app.router.add_get("/metrics", metrics_endpoint)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8081)
        await site.start()

        self._health_server = runner
        logger.info("Health server started on port 8081")


async def main() -> None:
    """Main entry point with supervisor and OpenTelemetry."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize OpenTelemetry tracing
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if otlp_endpoint:
        from services.agent_orchestrator.telemetry import init_tracing
        init_tracing("astra-agent-orchestrator", otlp_endpoint)
        logger.info("OpenTelemetry tracing initialized with endpoint: %s", otlp_endpoint)
    else:
        from services.agent_orchestrator.telemetry import get_tracer
        get_tracer()  # Initialize noop tracer
        logger.info("OpenTelemetry tracing initialized (noop - no OTLP endpoint)")

    settings = Settings()
    orchestrator = AgentOrchestrator(settings)

    # Create supervisor with config
    supervisor = Supervisor(SupervisorConfig(
        max_restarts=10,
        restart_window_seconds=600,
        base_backoff_seconds=1.0,
        max_backoff_seconds=60.0,
        backoff_multiplier=2.0,
    ))

    async def run_orchestrator():
        await orchestrator.run()

    try:
        await supervisor.run(run_orchestrator)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Supervisor exited with code %d", e.code)
            sys.exit(e.code)
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)
    finally:
        # Shutdown OpenTelemetry
        from services.agent_orchestrator.telemetry import shutdown_tracing
        shutdown_tracing()
        logger.info("OpenTelemetry tracing shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
