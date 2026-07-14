"""Content Schedule Service — Business logic for recurring content publishing schedules."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.common import now
from app.domain.entities.content.content_publish import ContentPublish
from app.domain.entities.content.content_schedule import ContentSchedule
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from app.domain.services.publishing.adapters import get_adapter

if TYPE_CHECKING:
    from app.infrastructure.db.repositories.content.content_publish_repository import (
        ContentPublishRepository,
    )
    from app.infrastructure.db.repositories.content.content_repository import (
        ContentRepositoryImpl,
    )
    from app.infrastructure.db.repositories.content.content_schedule_repository import (
        ContentScheduleRepository,
    )


class ContentScheduleService:
    """Service for managing recurring content schedules."""

    def __init__(
        self,
        repo: "ContentScheduleRepository",
        content_repo: "ContentRepositoryImpl | None" = None,
        publish_repo: "ContentPublishRepository | None" = None,
    ):
        self.repo = repo
        self._content_repo = content_repo
        self._publish_repo = publish_repo

    async def _get_content(self, content_id: UUID) -> None:
        """Validate content exists."""
        if self._content_repo is None:
            raise ValidationError("Content repository not available")
        content = await self._content_repo.find_by_id(content_id)
        if content is None:
            raise EntityNotFoundError("Content", str(content_id))

    async def _publish_content(self, schedule: ContentSchedule) -> ContentPublish | None:
        """Publish content according to schedule."""
        if self._publish_repo is None or self._content_repo is None:
            raise ValidationError("Publishing repository not available")

        adapter = get_adapter(schedule.platform)
        if adapter is None:
            raise ValidationError(f"No adapter for platform: {schedule.platform}")

        content = await self._content_repo.find_by_id(schedule.content_id)
        if not content:
            raise EntityNotFoundError("Content", str(schedule.content_id))

        # Create publish record
        publish = ContentPublish.create(
            content_id=schedule.content_id,
            platform=schedule.platform,
            scheduled_at=None,  # Immediate publish
            metadata=schedule.metadata,
        )
        publish.mark_publishing()
        await self._publish_repo.save(publish)

        try:
            url = await adapter.publish(content=content, metadata=schedule.metadata)
            publish.mark_published(url)
            return await self._publish_repo.save(publish)
        except Exception as e:
            publish.mark_failed(str(e))
            await self._publish_repo.save(publish)
            raise

    async def create_schedule(
        self,
        organization_id: UUID,
        content_id: UUID,
        name: str,
        platform: str,
        cron_expression: str,
        timezone: str = "UTC",
        max_runs: int | None = None,
        metadata: dict | None = None,
        created_by: UUID | None = None,
    ) -> ContentSchedule:
        """Create a new recurring content schedule."""
        await self._get_content(content_id)

        schedule = ContentSchedule.create(
            organization_id=organization_id,
            content_id=content_id,
            name=name,
            platform=platform,
            cron_expression=cron_expression,
            timezone=timezone,
            max_runs=max_runs,
            metadata=metadata,
            created_by=created_by,
        )

        # Calculate next run time
        from app.domain.services.workflow_scheduler import CronExpression

        try:
            cron = CronExpression.from_string(cron_expression)
            schedule.next_run_at = cron.next_trigger_time()
        except ValueError as e:
            raise ValidationError(f"Invalid cron expression: {e}")

        return await self.repo.save(schedule)

    async def get_schedule(self, schedule_id: UUID) -> ContentSchedule | None:
        """Get a schedule by ID."""
        return await self.repo.find_by_id(schedule_id)

    async def list_schedules(
        self,
        organization_id: UUID,
        status: str | None = None,
    ) -> list[ContentSchedule]:
        """List all schedules for an organization."""
        return await self.repo.find_by_organization(organization_id, status=status)

    async def get_content_schedules(self, content_id: UUID) -> list[ContentSchedule]:
        """Get all schedules for a specific content item."""
        return await self.repo.find_by_content(content_id)

    async def update_schedule(
        self,
        schedule_id: UUID,
        name: str | None = None,
        cron_expression: str | None = None,
        timezone: str | None = None,
        max_runs: int | None = None,
        metadata: dict | None = None,
    ) -> ContentSchedule | None:
        """Update a schedule."""
        schedule = await self.repo.find_by_id(schedule_id)
        if schedule is None:
            raise EntityNotFoundError("ContentSchedule", str(schedule_id))

        if name is not None:
            if not name.strip():
                raise ValidationError("Schedule name cannot be empty")
            schedule.name = name.strip()

        if cron_expression is not None:
            # Validate cron expression
            from app.domain.services.workflow_scheduler import CronExpression

            try:
                cron = CronExpression.from_string(cron_expression)
                schedule.cron_expression = cron_expression
                schedule.next_run_at = cron.next_trigger_time()
            except ValueError as e:
                raise ValidationError(f"Invalid cron expression: {e}")

        if timezone is not None:
            schedule.timezone = timezone

        if max_runs is not None:
            if max_runs < 1:
                raise ValidationError("max_runs must be at least 1")
            schedule.max_runs = max_runs

        if metadata is not None:
            schedule.metadata = metadata

        schedule.updated_at = now()
        return await self.repo.save(schedule)

    async def pause_schedule(self, schedule_id: UUID) -> ContentSchedule | None:
        """Pause a schedule."""
        schedule = await self.repo.find_by_id(schedule_id)
        if schedule is None:
            raise EntityNotFoundError("ContentSchedule", str(schedule_id))

        schedule.pause()
        return await self.repo.save(schedule)

    async def resume_schedule(self, schedule_id: UUID) -> ContentSchedule | None:
        """Resume a paused schedule."""
        schedule = await self.repo.find_by_id(schedule_id)
        if schedule is None:
            raise EntityNotFoundError("ContentSchedule", str(schedule_id))

        schedule.resume()
        # Recalculate next run
        from app.domain.services.workflow_scheduler import CronExpression

        cron = CronExpression.from_string(schedule.cron_expression)
        schedule.next_run_at = cron.next_trigger_time()

        return await self.repo.save(schedule)

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete a schedule."""
        schedule = await self.repo.find_by_id(schedule_id)
        if schedule is None:
            raise EntityNotFoundError("ContentSchedule", str(schedule_id))

        await self.repo.delete(schedule_id)
        return True

    async def get_due_schedules(self, current_time: datetime | None = None) -> list[ContentSchedule]:
        """Get all schedules that are due to run."""
        return await self.repo.find_due_schedules(current_time)

    async def process_due_schedules(self, current_time: datetime | None = None) -> dict:
        """Process all due schedules - publish content and update schedule state."""
        due_schedules = await self.get_due_schedules(current_time)
        results = {
            "processed": 0,
            "published": 0,
            "failed": 0,
            "errors": [],
        }

        for schedule in due_schedules:
            if not schedule.can_run(current_time):
                continue

            results["processed"] += 1

            try:
                # Publish the content
                await self._publish_content(schedule)

                # Update schedule state
                schedule.mark_run()
                await self.repo.save(schedule)

                results["published"] += 1
            except Exception as e:
                schedule.mark_error(str(e))
                await self.repo.save(schedule)
                results["failed"] += 1
                results["errors"].append({
                    "schedule_id": str(schedule.id),
                    "error": str(e),
                })

        return results
