"""Content Schedule Worker — Background worker that processes due recurring content schedules.

This worker runs in the FastAPI lifespan and periodically checks for schedules
that are due to run, publishing the content and updating schedule state.
"""

import asyncio
import contextlib
import logging

from app.application.use_cases.content.content_schedule_service import ContentScheduleService
from app.config import config
from app.infrastructure.db.repositories.content.content_publish_repository import (
    ContentPublishRepository,
)
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl
from app.infrastructure.db.repositories.content.content_schedule_repository import (
    ContentScheduleRepository,
)
from app.infrastructure.db.session import AsyncSessionFactory

logger = logging.getLogger(__name__)


class ContentScheduleWorker:
    """Background worker that processes due content schedules."""

    def __init__(
        self,
        session_factory: AsyncSessionFactory,
        poll_interval_seconds: int | None = None,
    ):
        self._session_factory = session_factory
        self._poll_interval = poll_interval_seconds or config.content_schedule_poll_interval
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the worker."""
        if self._running:
            logger.warning("ContentScheduleWorker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("ContentScheduleWorker started (poll interval: %ds)", self._poll_interval)

    async def stop(self) -> None:
        """Stop the worker."""
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("ContentScheduleWorker stopped")

    async def _poll_loop(self) -> None:
        """Run the polling loop."""
        while self._running:
            try:
                await self._process_due_schedules()
            except Exception:
                logger.exception("Error in ContentScheduleWorker poll loop")
            await asyncio.sleep(self._poll_interval)

    async def _process_due_schedules(self) -> None:
        """Process all due schedules."""
        async with self._session_factory() as session:
            schedule_repo = ContentScheduleRepository(session)
            content_repo = ContentRepositoryImpl(session)
            publish_repo = ContentPublishRepository(session)

            service = ContentScheduleService(
                schedule_repo,
                content_repo,
                publish_repo,
            )

            results = await service.process_due_schedules()

            if results["processed"] > 0:
                logger.info(
                    "Processed %d due schedules: %d published, %d failed",
                    results["processed"],
                    results["published"],
                    results["failed"],
                )

                if results["errors"]:
                    for error in results["errors"]:
                        logger.error(
                            "Schedule %s failed: %s",
                            error["schedule_id"],
                            error["error"],
                        )

    async def trigger_now(self) -> dict:
        """Manually trigger processing of due schedules."""
        async with self._session_factory() as session:
            schedule_repo = ContentScheduleRepository(session)
            content_repo = ContentRepositoryImpl(session)
            publish_repo = ContentPublishRepository(session)

            service = ContentScheduleService(
                schedule_repo,
                content_repo,
                publish_repo,
            )

            return await service.process_due_schedules()


# Global instance
content_schedule_worker: ContentScheduleWorker | None = None


async def get_content_schedule_worker() -> ContentScheduleWorker | None:
    """Get the global worker instance."""
    return content_schedule_worker
