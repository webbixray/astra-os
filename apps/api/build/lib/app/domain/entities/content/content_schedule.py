"""Content Schedule Entity — Domain entity for recurring content publishing schedules."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError


class ScheduleStatus(str, Enum):
    """Status of a content schedule."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


VALID_PLATFORMS: list[str] = [
    "website",
    "twitter",
    "linkedin",
    "facebook",
    "instagram",
    "email",
]


def _raise_invalid_field(field_name: str, part: str) -> None:
    """Raise ValidationError for invalid cron field."""
    raise ValidationError(f"Invalid {field_name} field: {part}")


def _validate_cron_field(part: str, min_val: int, max_val: int, field_name: str) -> None:
    """Validate a single cron field."""
    if part == "*":
        return

    if "/" in part:
        _validate_step_field(part, min_val, max_val, field_name)
    elif "," in part:
        _validate_list_field(part, min_val, max_val, field_name)
    elif "-" in part:
        _validate_range_field(part, min_val, max_val, field_name)
    else:
        _validate_single_value(part, min_val, max_val, field_name)


def _validate_step_field(part: str, min_val: int, max_val: int, field_name: str) -> None:
    """Validate step field (e.g., */5, 10/2)."""
    base, step = part.split("/")
    if base != "*":
        _validate_single_value(base, min_val, max_val, field_name)
    try:
        step_val = int(step)
        if step_val <= 0:
            _raise_invalid_field(field_name, part)
    except ValueError:
        _raise_invalid_field(field_name, part)


def _validate_list_field(part: str, min_val: int, max_val: int, field_name: str) -> None:
    """Validate comma-separated list field (e.g., 1,3,5)."""
    for sub_part in part.split(","):
        _validate_single_value(sub_part, min_val, max_val, field_name)


def _validate_range_field(part: str, min_val: int, max_val: int, field_name: str) -> None:
    """Validate range field (e.g., 1-5)."""
    start, end = part.split("-")
    try:
        s, e = int(start), int(end)
        if not (min_val <= s <= max_val) or not (min_val <= e <= max_val) or s > e:
            _raise_invalid_field(field_name, part)
    except ValueError:
        _raise_invalid_field(field_name, part)


def _validate_single_value(part: str, min_val: int, max_val: int, field_name: str) -> None:
    """Validate a single integer value."""
    try:
        val = int(part)
        if not (min_val <= val <= max_val):
            _raise_invalid_field(field_name, part)
    except ValueError:
        _raise_invalid_field(field_name, part)


def _raise_invalid_field(field_name: str, part: str) -> None:
    """Raise ValidationError for invalid cron field."""
    raise ValidationError(f"Invalid {field_name} field: {part}")


@dataclass
class ContentSchedule:
    """Recurring schedule for publishing content to a platform."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    content_id: UUID = field(default_factory=uuid4)
    name: str = ""
    platform: str = ""
    cron_expression: str = ""
    timezone: str = "UTC"
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    run_count: int = 0
    max_runs: int | None = None
    metadata: dict = field(default_factory=dict)
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    # Validation constants
    VALID_PLATFORMS: ClassVar[list[str]] = VALID_PLATFORMS

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Validate the schedule."""
        if not self.name or not self.name.strip():
            raise ValidationError("Schedule name is required")
        if self.platform not in self.VALID_PLATFORMS:
            raise ValidationError(
                f"Invalid platform: {self.platform}. Must be one of {self.VALID_PLATFORMS}"
            )
        if not self.cron_expression or not self.cron_expression.strip():
            raise ValidationError("Cron expression is required")
        self._validate_cron_expression()

    def _validate_cron_expression(self) -> None:
        """Validate cron expression has 5 fields."""
        parts = self.cron_expression.strip().split()
        if len(parts) != 5:
            raise ValidationError(
                f"Cron expression must have 5 fields (minute hour day month weekday), "
                f"got {len(parts)}: {self.cron_expression}"
            )
        # Basic field validation
        field_names = ["minute", "hour", "day", "month", "weekday"]
        ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
        for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges, strict=True)):
            _validate_cron_field(part, min_val, max_val, field_names[i])

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        content_id: UUID,
        name: str,
        platform: str,
        cron_expression: str,
        created_by: UUID,
        *,
        timezone: str = "UTC",
        max_runs: int | None = None,
        metadata: dict | None = None,
    ) -> "ContentSchedule":
        """Create a new content schedule."""
        schedule = cls(
            organization_id=organization_id,
            content_id=content_id,
            name=name,
            platform=platform,
            cron_expression=cron_expression,
            timezone=timezone,
            created_by=created_by,
            max_runs=max_runs,
            metadata=metadata or {},
        )
        # Calculate first run time
        schedule.next_run_at = schedule._calculate_next_run()
        return schedule

    def _calculate_next_run(self) -> datetime | None:
        """Calculate the next run time based on cron expression."""
        # Use the existing WorkflowScheduler's CronExpression for consistency
        from app.domain.services.workflow_scheduler import CronExpression

        try:
            cron = CronExpression.from_string(self.cron_expression)
            return cron.next_trigger_time()
        except Exception:
            return None

    def calculate_next_run(self) -> None:
        """Update next_run_at based on cron expression."""
        self.next_run_at = self._calculate_next_run()
        self.updated_at = now()

    def mark_run(self) -> None:
        """Mark a successful run."""
        self.last_run_at = now()
        self.run_count += 1
        self.updated_at = now()

        # Calculate next run
        self.calculate_next_run()

        # Check if completed
        if self.max_runs is not None and self.run_count >= self.max_runs:
            self.status = ScheduleStatus.COMPLETED
            self.next_run_at = None

    def mark_error(self, error_message: str) -> None:
        """Mark schedule as errored."""
        self.status = ScheduleStatus.ERROR
        self.metadata["last_error"] = error_message
        self.metadata["last_error_at"] = now().isoformat()
        self.updated_at = now()

    def pause(self) -> None:
        """Pause the schedule."""
        self.status = ScheduleStatus.PAUSED
        self.updated_at = now()

    def resume(self) -> None:
        """Resume the schedule."""
        if self.status == ScheduleStatus.PAUSED:
            self.status = ScheduleStatus.ACTIVE
            self.calculate_next_run()
            self.updated_at = now()

    def is_due(self, current_time: datetime | None = None) -> bool:
        """Check if the schedule is due to run."""
        if self.status != ScheduleStatus.ACTIVE:
            return False
        if self.next_run_at is None:
            return False
        current = current_time or now()
        return self.next_run_at <= current

    def can_run(self, current_time: datetime | None = None) -> bool:
        """Check if schedule can run (active, due, not completed)."""
        if self.status != ScheduleStatus.ACTIVE:
            return False
        if self.max_runs is not None and self.run_count >= self.max_runs:
            return False
        return self.is_due(current_time)
