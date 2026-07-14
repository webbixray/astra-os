"""Workflow Scheduler — Cron, event-driven, and webhook triggers for workflows.

M5 Workflow Engine: Allows workflows to be triggered automatically based on
schedules (cron), domain events, or incoming webhooks.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.events.event_bus import (
    DomainEvent,
    DomainEventType,
    EventBus,
)

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    CRON = "cron"
    EVENT = "event"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class ScheduleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class CronExpression:
    """Parsed cron expression with 5 fields: minute, hour, day_of_month, month, day_of_week."""

    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month: str = "*"
    day_of_week: str = "*"

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        patterns = {
            "minute": (r"^(\*|[0-5]?\d)(/[0-9]+)?$", "0-59"),
            "hour": (r"^(\*|[01]?\d|2[0-3])(/[0-9]+)?$", "0-23"),
            "day_of_month": (r"^(\*|[12]?\d|3[01])(/[0-9]+)?$", "1-31"),
            "month": (r"^(\*|[1-9]|1[0-2])(/[0-9]+)?$", "1-12"),
            "day_of_week": (r"^(\*|[0-6])(/[0-9]+)?$", "0-6"),
        }
        fields = {
            "minute": self.minute,
            "hour": self.hour,
            "day_of_month": self.day_of_month,
            "month": self.month,
            "day_of_week": self.day_of_week,
        }
        for name, (pattern, _range) in patterns.items():
            value = fields[name]
            if not re.match(pattern, value):
                raise ValueError(
                    f"Invalid cron field '{name}': '{value}'. Expected range {_range}."
                )

    @classmethod
    def from_string(cls, cron_str: str) -> CronExpression:
        parts = cron_str.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Cron expression must have 5 fields, got {len(parts)}: '{cron_str}'"
            )
        return cls(
            minute=parts[0],
            hour=parts[1],
            day_of_month=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

    def should_trigger(self, current: datetime | None = None) -> bool:
        """Check if this cron expression should trigger at the given time.

        Cron day_of_week convention: 0=Sunday, 1=Monday, ..., 6=Saturday.
        Python weekday(): 0=Monday, ..., 6=Sunday.
        We convert Python weekday to cron convention before matching.
        """
        current = current or now()
        # Convert Python weekday (0=Mon) to cron day_of_week (0=Sun)
        cron_weekday = (current.weekday() + 1) % 7
        return (
            self._matches_field(self.minute, current.minute, 0, 59)
            and self._matches_field(self.hour, current.hour, 0, 23)
            and self._matches_field(self.day_of_month, current.day, 1, 31)
            and self._matches_field(self.month, current.month, 1, 12)
            and self._matches_field(self.day_of_week, cron_weekday, 0, 6)
        )

    def _matches_field(self, pattern: str, value: int, min_val: int, max_val: int) -> bool:
        if "/" in pattern:
            base, step_str = pattern.split("/")
            step = int(step_str)
            if base == "*":
                return (value - min_val) % step == 0
            base_val = int(base)
            return value >= base_val and (value - base_val) % step == 0
        if pattern == "*":
            return True
        return int(pattern) == value

    def to_string(self) -> str:
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"

    def next_trigger_time(self, after: datetime | None = None) -> datetime:
        """Calculate the next trigger time after the given time (simplified)."""
        current = after or now()
        # Advance by 1 minute and check (simplified — not optimized for production cron)
        candidate = current + timedelta(minutes=1)
        candidate = candidate.replace(second=0, microsecond=0)
        for _ in range(60 * 24 * 365):  # Max 1 year ahead
            if self.should_trigger(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        raise ValueError("Could not find next trigger time within 1 year")


WorkflowTriggerHandler = Callable[[UUID, dict[str, Any]], Awaitable[None]]


@dataclass
class WorkflowSchedule:
    """A scheduled trigger for a workflow."""

    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    trigger_type: TriggerType = TriggerType.MANUAL
    cron_expression: str | None = None
    event_type: str | None = None
    webhook_secret: str | None = None
    is_active: bool = True
    last_triggered_at: datetime | None = None
    next_trigger_at: datetime | None = None
    trigger_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "organization_id": str(self.organization_id),
            "trigger_type": self.trigger_type.value,
            "cron_expression": self.cron_expression,
            "event_type": self.event_type,
            "is_active": self.is_active,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "next_trigger_at": self.next_trigger_at.isoformat() if self.next_trigger_at else None,
            "trigger_count": self.trigger_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkflowScheduler:
    """Manages workflow triggers — cron, event-driven, and webhook-based.

    This scheduler runs in-process and evaluates triggers on a polling loop.
    In production, this would be backed by Temporal or a dedicated scheduler service.
    """

    def __init__(self) -> None:
        self._schedules: dict[UUID, WorkflowSchedule] = {}
        self._handlers: dict[UUID, WorkflowTriggerHandler] = {}
        self._event_unsubscribers: list[Callable[[], None]] = []
        self._running = False
        self._poll_task: asyncio.Task[None] | None = None
        self._poll_interval_seconds: int = 30

    def create_schedule(
        self,
        workflow_id: UUID,
        organization_id: UUID,
        trigger_type: TriggerType,
        cron_expression: str | None = None,
        event_type: str | None = None,
        webhook_secret: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowSchedule:
        """Create a new workflow schedule."""
        if trigger_type == TriggerType.CRON and not cron_expression:
            raise ValueError("Cron expression is required for cron triggers")

        if trigger_type == TriggerType.CRON and cron_expression:
            cron = CronExpression.from_string(cron_expression)
            next_trigger = cron.next_trigger_time()
        else:
            next_trigger = None

        schedule = WorkflowSchedule(
            workflow_id=workflow_id,
            organization_id=organization_id,
            trigger_type=trigger_type,
            cron_expression=cron_expression,
            event_type=event_type,
            webhook_secret=webhook_secret,
            next_trigger_at=next_trigger,
            metadata=metadata or {},
        )
        self._schedules[schedule.id] = schedule
        return schedule

    def get_schedule(self, schedule_id: UUID) -> WorkflowSchedule | None:
        return self._schedules.get(schedule_id)

    def list_schedules(
        self,
        workflow_id: UUID | None = None,
        organization_id: UUID | None = None,
        trigger_type: TriggerType | None = None,
    ) -> list[WorkflowSchedule]:
        results = list(self._schedules.values())
        if workflow_id is not None:
            results = [s for s in results if s.workflow_id == workflow_id]
        if organization_id is not None:
            results = [s for s in results if s.organization_id == organization_id]
        if trigger_type is not None:
            results = [s for s in results if s.trigger_type == trigger_type]
        return results

    def pause_schedule(self, schedule_id: UUID) -> WorkflowSchedule | None:
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.is_active = False
            schedule.updated_at = now()
        return schedule

    def resume_schedule(self, schedule_id: UUID) -> WorkflowSchedule | None:
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.is_active = True
            schedule.updated_at = now()
            if schedule.trigger_type == TriggerType.CRON and schedule.cron_expression:
                cron = CronExpression.from_string(schedule.cron_expression)
                schedule.next_trigger_at = cron.next_trigger_time()
        return schedule

    def delete_schedule(self, schedule_id: UUID) -> bool:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def register_handler(
        self, schedule_id: UUID, handler: WorkflowTriggerHandler
    ) -> None:
        """Register a handler to be called when a schedule triggers."""
        self._handlers[schedule_id] = handler

    def register_event_handler(
        self,
        schedule_id: UUID,
        event_type: DomainEventType,
        handler: WorkflowTriggerHandler,
    ) -> None:
        """Register an event-driven trigger. Subscribes to the EventBus."""
        self._handlers[schedule_id] = handler

        async def _on_event(event: DomainEvent) -> None:
            schedule = self._schedules.get(schedule_id)
            if schedule and schedule.is_active:
                await self._trigger_workflow(schedule, event.data)

        unsub = EventBus.subscribe(event_type, _on_event)
        self._event_unsubscribers.append(unsub)

    async def trigger_webhook(
        self,
        schedule_id: UUID,
        payload: dict[str, Any],
        secret: str | None = None,
    ) -> bool:
        """Process an incoming webhook trigger."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False
        if not schedule.is_active:
            return False
        if schedule.trigger_type != TriggerType.WEBHOOK:
            return False
        if schedule.webhook_secret and schedule.webhook_secret != secret:
            return False

        await self._trigger_workflow(schedule, payload)
        return True

    async def _trigger_workflow(
        self, schedule: WorkflowSchedule, context: dict[str, Any]
    ) -> None:
        """Execute the workflow associated with a schedule."""
        handler = self._handlers.get(schedule.id)
        if not handler:
            logger.warning(
                "No handler registered for schedule %s (workflow %s)",
                schedule.id,
                schedule.workflow_id,
            )
            return

        schedule.last_triggered_at = now()
        schedule.trigger_count += 1
        schedule.updated_at = now()

        if schedule.trigger_type == TriggerType.CRON and schedule.cron_expression:
            cron = CronExpression.from_string(schedule.cron_expression)
            try:
                schedule.next_trigger_at = cron.next_trigger_time(schedule.last_triggered_at)
            except ValueError:
                logger.error("Could not calculate next trigger for schedule %s", schedule.id)

        try:
            await handler(schedule.workflow_id, context)
            logger.info(
                "Workflow %s triggered by schedule %s (count: %d)",
                schedule.workflow_id,
                schedule.id,
                schedule.trigger_count,
            )
        except Exception as e:
            logger.error(
                "Failed to trigger workflow %s: %s", schedule.workflow_id, e
            )
            schedule.is_active = False
            raise

    async def evaluate_cron_triggers(self) -> list[UUID]:
        """Evaluate all cron schedules and trigger any that are due. Returns triggered schedule IDs."""
        triggered: list[UUID] = []
        current = now()
        for schedule in list(self._schedules.values()):
            if (
                schedule.is_active
                and schedule.trigger_type == TriggerType.CRON
                and schedule.cron_expression
            ):
                cron = CronExpression.from_string(schedule.cron_expression)
                if cron.should_trigger(current):
                    await self._trigger_workflow(schedule, {"trigger": "cron", "time": current.isoformat()})
                    triggered.append(schedule.id)
        return triggered

    async def start(self) -> None:
        """Start the polling loop for cron triggers."""
        if self._running:
            return
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("WorkflowScheduler started (poll interval: %ds)", self._poll_interval_seconds)

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        for unsub in self._event_unsubscribers:
            unsub()
        self._event_unsubscribers.clear()
        logger.info("WorkflowScheduler stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self.evaluate_cron_triggers()
            except Exception:
                logger.exception("Error evaluating cron triggers")
            await asyncio.sleep(self._poll_interval_seconds)

    def get_stats(self) -> dict[str, Any]:
        """Return scheduler statistics."""
        schedules = list(self._schedules.values())
        return {
            "total_schedules": len(schedules),
            "active_schedules": sum(1 for s in schedules if s.is_active),
            "cron_schedules": sum(1 for s in schedules if s.trigger_type == TriggerType.CRON),
            "event_schedules": sum(1 for s in schedules if s.trigger_type == TriggerType.EVENT),
            "webhook_schedules": sum(1 for s in schedules if s.trigger_type == TriggerType.WEBHOOK),
            "manual_schedules": sum(1 for s in schedules if s.trigger_type == TriggerType.MANUAL),
            "total_triggers": sum(s.trigger_count for s in schedules),
            "is_running": self._running,
        }


# Singleton
workflow_scheduler = WorkflowScheduler()
