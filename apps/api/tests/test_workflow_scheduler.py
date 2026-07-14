"""Tests for Workflow Scheduler — M5 Workflow Engine."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.events.event_bus import DomainEvent, DomainEventType, EventBus
from app.domain.services.workflow_scheduler import (
    CronExpression,
    TriggerType,
    WorkflowSchedule,
    WorkflowScheduler,
)

# ---------------------------------------------------------------------------
# CronExpression tests
# ---------------------------------------------------------------------------

class TestCronExpression:
    def test_parse_valid_cron(self):
        cron = CronExpression.from_string("0 9 * * *")
        assert cron.minute == "0"
        assert cron.hour == "9"
        assert cron.day_of_month == "*"
        assert cron.month == "*"
        assert cron.day_of_week == "*"

    def test_parse_cron_too_few_fields(self):
        with pytest.raises(ValueError, match="5 fields"):
            CronExpression.from_string("0 9 * *")

    def test_parse_cron_too_many_fields(self):
        with pytest.raises(ValueError, match="5 fields"):
            CronExpression.from_string("0 9 * * * *")

    def test_invalid_minute(self):
        with pytest.raises(ValueError, match="minute"):
            CronExpression(minute="60", hour="*", day_of_month="*", month="*", day_of_week="*")

    def test_invalid_hour(self):
        with pytest.raises(ValueError, match="hour"):
            CronExpression(minute="0", hour="25", day_of_month="*", month="*", day_of_week="*")

    def test_invalid_day_of_month(self):
        with pytest.raises(ValueError, match="day_of_month"):
            CronExpression(minute="0", hour="9", day_of_month="32", month="*", day_of_week="*")

    def test_invalid_month(self):
        with pytest.raises(ValueError, match="month"):
            CronExpression(minute="0", hour="9", day_of_month="1", month="13", day_of_week="*")

    def test_invalid_day_of_week(self):
        with pytest.raises(ValueError, match="day_of_week"):
            CronExpression(minute="0", hour="9", day_of_month="1", month="1", day_of_week="7")

    def test_valid_cron_fields(self):
        cron = CronExpression(minute="30", hour="14", day_of_month="15", month="6", day_of_week="1")
        assert cron.minute == "30"
        assert cron.hour == "14"

    def test_should_trigger_wildcard(self):
        cron = CronExpression.from_string("* * * * *")
        assert cron.should_trigger(datetime(2026, 7, 12, 10, 30, tzinfo=UTC))

    def test_should_trigger_specific_time(self):
        cron = CronExpression.from_string("0 9 * * *")
        assert cron.should_trigger(datetime(2026, 7, 12, 9, 0, tzinfo=UTC))
        assert not cron.should_trigger(datetime(2026, 7, 12, 9, 1, tzinfo=UTC))
        assert not cron.should_trigger(datetime(2026, 7, 12, 10, 0, tzinfo=UTC))

    def test_should_trigger_step(self):
        cron = CronExpression.from_string("*/15 * * * *")
        assert cron.should_trigger(datetime(2026, 7, 12, 10, 0, tzinfo=UTC))
        assert cron.should_trigger(datetime(2026, 7, 12, 10, 15, tzinfo=UTC))
        assert cron.should_trigger(datetime(2026, 7, 12, 10, 30, tzinfo=UTC))
        assert cron.should_trigger(datetime(2026, 7, 12, 10, 45, tzinfo=UTC))
        assert not cron.should_trigger(datetime(2026, 7, 12, 10, 10, tzinfo=UTC))

    def test_should_trigger_specific_weekday(self):
        # Cron day_of_week: 1=Monday
        cron = CronExpression.from_string("0 9 * * 1")
        monday = datetime(2026, 7, 13, 9, 0, tzinfo=UTC)  # Monday
        tuesday = datetime(2026, 7, 14, 9, 0, tzinfo=UTC)  # Tuesday
        assert cron.should_trigger(monday)
        assert not cron.should_trigger(tuesday)

    def test_to_string(self):
        cron = CronExpression(minute="0", hour="9", day_of_month="*", month="*", day_of_week="1")
        assert cron.to_string() == "0 9 * * 1"

    def test_next_trigger_time(self):
        cron = CronExpression.from_string("0 9 * * *")
        after = datetime(2026, 7, 12, 10, 0, 0, tzinfo=UTC)
        next_t = cron.next_trigger_time(after)
        # Next 9:00 after 10:00 should be next day
        assert next_t.hour == 9
        assert next_t.minute == 0
        assert next_t > after


# ---------------------------------------------------------------------------
# WorkflowSchedule tests
# ---------------------------------------------------------------------------

class TestWorkflowSchedule:
    def test_schedule_creation(self):
        schedule = WorkflowSchedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        assert schedule.is_active is True
        assert schedule.trigger_count == 0
        assert schedule.trigger_type == TriggerType.CRON

    def test_schedule_to_dict(self):
        wf_id = uuid4()
        org_id = uuid4()
        schedule = WorkflowSchedule(
            id=uuid4(),
            workflow_id=wf_id,
            organization_id=org_id,
            trigger_type=TriggerType.EVENT,
            event_type="campaign.activated",
        )
        d = schedule.to_dict()
        assert d["workflow_id"] == str(wf_id)
        assert d["organization_id"] == str(org_id)
        assert d["trigger_type"] == "event"
        assert d["event_type"] == "campaign.activated"
        assert d["is_active"] is True
        assert d["trigger_count"] == 0


# ---------------------------------------------------------------------------
# WorkflowScheduler tests
# ---------------------------------------------------------------------------

class TestWorkflowScheduler:
    def setup_method(self):
        self.scheduler = WorkflowScheduler()

    def test_create_cron_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        assert schedule.id in self.scheduler._schedules
        assert schedule.trigger_type == TriggerType.CRON
        assert schedule.cron_expression == "0 9 * * *"
        assert schedule.next_trigger_at is not None

    def test_create_cron_schedule_without_expression_raises(self):
        with pytest.raises(ValueError, match="Cron expression is required"):
            self.scheduler.create_schedule(
                workflow_id=uuid4(),
                organization_id=uuid4(),
                trigger_type=TriggerType.CRON,
            )

    def test_create_event_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
            event_type="campaign.activated",
        )
        assert schedule.trigger_type == TriggerType.EVENT
        assert schedule.event_type == "campaign.activated"

    def test_create_webhook_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
            webhook_secret="secret_123",
        )
        assert schedule.trigger_type == TriggerType.WEBHOOK
        assert schedule.webhook_secret == "secret_123"

    def test_create_manual_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        assert schedule.trigger_type == TriggerType.MANUAL

    def test_get_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        found = self.scheduler.get_schedule(schedule.id)
        assert found is not None
        assert found.id == schedule.id

    def test_get_nonexistent_schedule(self):
        assert self.scheduler.get_schedule(uuid4()) is None

    def test_list_schedules_all(self):
        for _ in range(3):
            self.scheduler.create_schedule(
                workflow_id=uuid4(),
                organization_id=uuid4(),
                trigger_type=TriggerType.MANUAL,
            )
        assert len(self.scheduler.list_schedules()) == 3

    def test_list_schedules_by_workflow(self):
        wf_id = uuid4()
        self.scheduler.create_schedule(
            workflow_id=wf_id,
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        results = self.scheduler.list_schedules(workflow_id=wf_id)
        assert len(results) == 1

    def test_list_schedules_by_organization(self):
        org_id = uuid4()
        self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=org_id,
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        results = self.scheduler.list_schedules(organization_id=org_id)
        assert len(results) == 1

    def test_list_schedules_by_type(self):
        self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
        )
        cron_results = self.scheduler.list_schedules(trigger_type=TriggerType.CRON)
        assert len(cron_results) == 1
        event_results = self.scheduler.list_schedules(trigger_type=TriggerType.EVENT)
        assert len(event_results) == 1

    def test_pause_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        paused = self.scheduler.pause_schedule(schedule.id)
        assert paused is not None
        assert paused.is_active is False

    def test_pause_nonexistent_schedule(self):
        assert self.scheduler.pause_schedule(uuid4()) is None

    def test_resume_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.pause_schedule(schedule.id)
        resumed = self.scheduler.resume_schedule(schedule.id)
        assert resumed is not None
        assert resumed.is_active is True

    def test_resume_cron_schedule_updates_next_trigger(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        self.scheduler.pause_schedule(schedule.id)
        schedule.next_trigger_at = None
        resumed = self.scheduler.resume_schedule(schedule.id)
        assert resumed is not None
        assert resumed.next_trigger_at is not None

    def test_delete_schedule(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        assert self.scheduler.delete_schedule(schedule.id) is True
        assert self.scheduler.get_schedule(schedule.id) is None

    def test_delete_nonexistent_schedule(self):
        assert self.scheduler.delete_schedule(uuid4()) is False


# ---------------------------------------------------------------------------
# Trigger execution tests
# ---------------------------------------------------------------------------

class TestWorkflowSchedulerExecution:
    def setup_method(self):
        self.scheduler = WorkflowScheduler()

    @pytest.mark.asyncio
    async def test_trigger_workflow_calls_handler(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.register_handler(schedule.id, handler)

        await self.scheduler._trigger_workflow(schedule, {"key": "value"})

        handler.assert_called_once()
        call_args = handler.call_args[0]
        assert call_args[0] == schedule.workflow_id
        assert call_args[1] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_trigger_increments_count(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.register_handler(schedule.id, handler)

        await self.scheduler._trigger_workflow(schedule, {})

        assert schedule.trigger_count == 1
        assert schedule.last_triggered_at is not None

    @pytest.mark.asyncio
    async def test_trigger_cron_updates_next_trigger(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        self.scheduler.register_handler(schedule.id, handler)

        await self.scheduler._trigger_workflow(schedule, {})

        assert schedule.next_trigger_at is not None
        assert schedule.trigger_count == 1

    @pytest.mark.asyncio
    async def test_trigger_without_handler_does_not_crash(self):
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        # No handler registered — should not raise
        await self.scheduler._trigger_workflow(schedule, {})

    @pytest.mark.asyncio
    async def test_trigger_handler_exception_marks_inactive(self):
        handler = AsyncMock(side_effect=RuntimeError("boom"))
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        self.scheduler.register_handler(schedule.id, handler)

        with pytest.raises(RuntimeError, match="boom"):
            await self.scheduler._trigger_workflow(schedule, {})

        assert schedule.is_active is False


# ---------------------------------------------------------------------------
# Webhook trigger tests
# ---------------------------------------------------------------------------

class TestWebhookTrigger:
    def setup_method(self):
        self.scheduler = WorkflowScheduler()

    @pytest.mark.asyncio
    async def test_trigger_webhook_success(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
            webhook_secret="secret_123",
        )
        self.scheduler.register_handler(schedule.id, handler)

        result = await self.scheduler.trigger_webhook(
            schedule.id, {"payload": "data"}, secret="secret_123"
        )
        assert result is True
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_webhook_wrong_secret(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
            webhook_secret="secret_123",
        )
        self.scheduler.register_handler(schedule.id, handler)

        result = await self.scheduler.trigger_webhook(
            schedule.id, {}, secret="wrong_secret"
        )
        assert result is False
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_webhook_no_secret_required(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
            webhook_secret=None,
        )
        self.scheduler.register_handler(schedule.id, handler)

        result = await self.scheduler.trigger_webhook(schedule.id, {}, secret=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_trigger_webhook_inactive_schedule(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
        )
        self.scheduler.register_handler(schedule.id, handler)
        self.scheduler.pause_schedule(schedule.id)

        result = await self.scheduler.trigger_webhook(schedule.id, {})
        assert result is False

    @pytest.mark.asyncio
    async def test_trigger_webhook_nonexistent_schedule(self):
        result = await self.scheduler.trigger_webhook(uuid4(), {})
        assert result is False

    @pytest.mark.asyncio
    async def test_trigger_webhook_wrong_type(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        self.scheduler.register_handler(schedule.id, handler)

        result = await self.scheduler.trigger_webhook(schedule.id, {})
        assert result is False


# ---------------------------------------------------------------------------
# Cron evaluation tests
# ---------------------------------------------------------------------------

class TestCronEvaluation:
    def setup_method(self):
        self.scheduler = WorkflowScheduler()

    @pytest.mark.asyncio
    async def test_evaluate_cron_triggers_matching(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="* * * * *",  # Every minute — always matches
        )
        self.scheduler.register_handler(schedule.id, handler)

        triggered = await self.scheduler.evaluate_cron_triggers()
        assert schedule.id in triggered
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_cron_skips_paused(self):
        handler = AsyncMock()
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="* * * * *",
        )
        self.scheduler.register_handler(schedule.id, handler)
        self.scheduler.pause_schedule(schedule.id)

        triggered = await self.scheduler.evaluate_cron_triggers()
        assert schedule.id not in triggered
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_cron_skips_non_matching(self):
        handler = AsyncMock()
        # Create a cron that only matches at 9:00 on Jan 1
        schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.CRON,
            cron_expression="0 0 1 1 *",
        )
        self.scheduler.register_handler(schedule.id, handler)

        triggered = await self.scheduler.evaluate_cron_triggers()
        assert schedule.id not in triggered

    @pytest.mark.asyncio
    async def test_evaluate_only_cron_triggers(self):
        handler = AsyncMock()
        event_schedule = self.scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
        )
        self.scheduler.register_handler(event_schedule.id, handler)

        triggered = await self.scheduler.evaluate_cron_triggers()
        assert event_schedule.id not in triggered


# ---------------------------------------------------------------------------
# Event-driven trigger tests
# ---------------------------------------------------------------------------

class TestEventDrivenTrigger:
    def setup_method(self):
        EventBus.reset()

    def teardown_method(self):
        EventBus.reset()

    @pytest.mark.asyncio
    async def test_event_trigger_fires_workflow(self):
        scheduler = WorkflowScheduler()
        handler = AsyncMock()
        schedule = scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
            event_type="campaign.activated",
        )
        scheduler.register_event_handler(schedule.id, DomainEventType.CAMPAIGN_ACTIVATED, handler)

        event = DomainEvent.create(
            event_type=DomainEventType.CAMPAIGN_ACTIVATED,
            aggregate_id=str(schedule.workflow_id),
            aggregate_type="campaign",
        )
        await EventBus.publish(event)

        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_trigger_not_fired_when_paused(self):
        scheduler = WorkflowScheduler()
        handler = AsyncMock()
        schedule = scheduler.create_schedule(
            workflow_id=uuid4(),
            organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
            event_type="campaign.activated",
        )
        scheduler.register_event_handler(schedule.id, DomainEventType.CAMPAIGN_ACTIVATED, handler)
        scheduler.pause_schedule(schedule.id)

        event = DomainEvent.create(
            event_type=DomainEventType.CAMPAIGN_ACTIVATED,
            aggregate_id=str(schedule.workflow_id),
            aggregate_type="campaign",
        )
        await EventBus.publish(event)

        handler.assert_not_called()


# ---------------------------------------------------------------------------
# Scheduler lifecycle tests
# ---------------------------------------------------------------------------

class TestSchedulerLifecycle:
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        scheduler = WorkflowScheduler()
        scheduler._poll_interval_seconds = 1  # Fast poll for testing
        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._poll_task is not None
        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        scheduler = WorkflowScheduler()
        await scheduler.start()
        task1 = scheduler._poll_task
        await scheduler.start()  # Should not create a new task
        assert scheduler._poll_task is task1
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_started(self):
        scheduler = WorkflowScheduler()
        await scheduler.stop()  # Should not raise


# ---------------------------------------------------------------------------
# Stats tests
# ---------------------------------------------------------------------------

class TestSchedulerStats:
    def test_stats_empty(self):
        scheduler = WorkflowScheduler()
        stats = scheduler.get_stats()
        assert stats["total_schedules"] == 0
        assert stats["active_schedules"] == 0
        assert stats["total_triggers"] == 0

    def test_stats_with_schedules(self):
        scheduler = WorkflowScheduler()
        scheduler.create_schedule(
            workflow_id=uuid4(), organization_id=uuid4(),
            trigger_type=TriggerType.CRON, cron_expression="0 9 * * *",
        )
        scheduler.create_schedule(
            workflow_id=uuid4(), organization_id=uuid4(),
            trigger_type=TriggerType.EVENT,
        )
        scheduler.create_schedule(
            workflow_id=uuid4(), organization_id=uuid4(),
            trigger_type=TriggerType.WEBHOOK,
        )
        scheduler.create_schedule(
            workflow_id=uuid4(), organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        stats = scheduler.get_stats()
        assert stats["total_schedules"] == 4
        assert stats["cron_schedules"] == 1
        assert stats["event_schedules"] == 1
        assert stats["webhook_schedules"] == 1
        assert stats["manual_schedules"] == 1

    def test_stats_reflect_paused(self):
        scheduler = WorkflowScheduler()
        s = scheduler.create_schedule(
            workflow_id=uuid4(), organization_id=uuid4(),
            trigger_type=TriggerType.MANUAL,
        )
        scheduler.pause_schedule(s.id)
        stats = scheduler.get_stats()
        assert stats["total_schedules"] == 1
        assert stats["active_schedules"] == 0
