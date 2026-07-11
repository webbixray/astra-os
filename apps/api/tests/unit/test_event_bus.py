from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.events.event_bus import (
    DomainEvent,
    DomainEventType,
    EventBus,
    EventPriority,
    event_handler,
)


@pytest.fixture(autouse=True)
def reset_bus() -> None:
    EventBus.reset()


class TestDomainEvent:
    def test_create_event(self) -> None:
        event = DomainEvent.create(
            event_type=DomainEventType.CAMPAIGN_CREATED,
            aggregate_id="camp-123",
            aggregate_type="campaign",
            data={"name": "Test"},
        )
        assert event.event_type == DomainEventType.CAMPAIGN_CREATED
        assert event.aggregate_id == "camp-123"
        assert event.data == {"name": "Test"}
        assert event.event_id is not None
        assert isinstance(event.timestamp, float)
        assert event.version == 1

    def test_create_without_data(self) -> None:
        event = DomainEvent.create(DomainEventType.USER_SIGNED_IN, "user-1", "user")
        assert event.data == {}

    def test_create_with_correlation_id(self) -> None:
        event = DomainEvent.create(
            DomainEventType.WORKFLOW_STARTED, "wf-1", "workflow",
            correlation_id="corr-abc",
        )
        assert event.correlation_id == "corr-abc"

    def test_create_with_priority(self) -> None:
        event = DomainEvent.create(
            DomainEventType.BILLING_PAYMENT_FAILED, "bill-1", "billing",
            priority=EventPriority.CRITICAL,
        )
        assert event.priority == EventPriority.CRITICAL

    def test_default_priority(self) -> None:
        event = DomainEvent.create(DomainEventType.CONTENT_CREATED, "c-1", "content")
        assert event.priority == EventPriority.NORMAL


class TestEventBusSingleton:
    def test_singleton(self) -> None:
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2

    def test_reset_clears_state(self) -> None:
        handler = AsyncMock()
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, handler)
        EventBus.reset()
        assert DomainEventType.CAMPAIGN_CREATED not in EventBus._subscribers
        assert EventBus._history == []


class TestEventBusSubscribe:
    async def test_subscribe_and_publish(self) -> None:
        handler = AsyncMock()
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, handler)

        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        handler.assert_awaited_once_with(event)

    async def test_subscribe_multiple_handlers(self) -> None:
        h1 = AsyncMock()
        h2 = AsyncMock()
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, h1)
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, h2)

        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        h1.assert_awaited_once()
        h2.assert_awaited_once()

    async def test_unsubscribe(self) -> None:
        handler = AsyncMock()
        unsubscribe = EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, handler)
        unsubscribe()

        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        handler.assert_not_awaited()

    async def test_only_called_for_subscribed_type(self) -> None:
        handler = AsyncMock()
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, handler)

        event = DomainEvent.create(DomainEventType.USER_SIGNED_IN, "u-1", "user")
        await EventBus.publish(event)

        handler.assert_not_awaited()


class TestEventBusGlobalSubscribers:
    async def test_global_subscriber_receives_all(self) -> None:
        handler = AsyncMock()
        EventBus.subscribe_all(handler)

        e1 = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        e2 = DomainEvent.create(DomainEventType.USER_SIGNED_IN, "u-1", "user")
        await EventBus.publish(e1)
        await EventBus.publish(e2)

        assert handler.await_count == 2

    async def test_global_unsubscribe(self) -> None:
        handler = AsyncMock()
        unsubscribe = EventBus.subscribe_all(handler)
        unsubscribe()

        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        handler.assert_not_awaited()


class TestEventBusErrorHandling:
    async def test_error_isolation(self) -> None:
        failing = AsyncMock(side_effect=ValueError("fail"))
        succeeding = AsyncMock()

        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, failing)
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, succeeding)

        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        succeeding.assert_awaited_once()


class TestEventBusHistory:
    async def test_events_added_to_history(self) -> None:
        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

        history = EventBus.get_history()
        assert len(history) == 1
        assert history[0].event_id == event.event_id

    async def test_history_filtered_by_type(self) -> None:
        e1 = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        e2 = DomainEvent.create(DomainEventType.USER_SIGNED_IN, "u-1", "user")
        await EventBus.publish(e1)
        await EventBus.publish(e2)

        campaigns = EventBus.get_history(event_type=DomainEventType.CAMPAIGN_CREATED)
        assert len(campaigns) == 1
        assert campaigns[0].event_type == DomainEventType.CAMPAIGN_CREATED

    async def test_history_respects_limit(self) -> None:
        for i in range(10):
            await EventBus.publish(
                DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, str(i), "campaign"),
            )

        recent = EventBus.get_history(limit=3)
        assert len(recent) == 3

    async def test_clear_history(self) -> None:
        await EventBus.publish(
            DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign"),
        )
        EventBus.clear_history()
        assert EventBus.get_history() == []

    async def test_history_max_size(self) -> None:
        EventBus._max_history = 5
        for i in range(10):
            await EventBus.publish(
                DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, str(i), "campaign"),
            )
        assert len(EventBus.get_history()) == 5


class TestEventHandlerDecorator:
    async def test_decorator_registers_handler(self) -> None:
        mock_handler = AsyncMock()

        decorated = event_handler(DomainEventType.CONTENT_PUBLISHED)(mock_handler)

        event = DomainEvent.create(DomainEventType.CONTENT_PUBLISHED, "c-1", "content")
        await EventBus.publish(event)

        mock_handler.assert_awaited_once_with(event)
        assert decorated is mock_handler


class TestEventBusConcurrency:
    async def test_publish_no_handlers_does_not_raise(self) -> None:
        event = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        await EventBus.publish(event)

    async def test_multiple_publishes(self) -> None:
        h1 = AsyncMock()
        h2 = AsyncMock()
        EventBus.subscribe(DomainEventType.CAMPAIGN_CREATED, h1)
        EventBus.subscribe(DomainEventType.TEAM_MEMBER_ADDED, h2)

        e1 = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign")
        e2 = DomainEvent.create(DomainEventType.TEAM_MEMBER_ADDED, "t-1", "team")
        e3 = DomainEvent.create(DomainEventType.CAMPAIGN_CREATED, "c-2", "campaign")

        await EventBus.publish(e1)
        await EventBus.publish(e2)
        await EventBus.publish(e3)

        assert h1.await_count == 2
        assert h2.await_count == 1


class TestDomainEventSerialization:
    def test_to_json_and_back(self) -> None:
        event = DomainEvent.create(
            event_type=DomainEventType.CAMPAIGN_CREATED,
            aggregate_id="camp-123",
            aggregate_type="campaign",
            data={"name": "Test Campaign", "budget": 5000},
            correlation_id="corr-abc",
            priority=EventPriority.HIGH,
        )
        json_str = event.to_json()
        restored = DomainEvent.from_json(json_str)

        assert restored.event_type == event.event_type
        assert restored.aggregate_id == event.aggregate_id
        assert restored.aggregate_type == event.aggregate_type
        assert restored.data == event.data
        assert restored.event_id == event.event_id
        assert restored.correlation_id == event.correlation_id
        assert restored.priority == event.priority
        assert restored.timestamp == event.timestamp

    def test_to_json_includes_source_instance(self) -> None:
        event = DomainEvent.create(
            DomainEventType.CAMPAIGN_CREATED, "c-1", "campaign"
        )
        json_str = event.to_json()
        import json
        payload = json.loads(json_str)
        assert "source_instance" in payload

    def test_roundtrip_preserves_all_event_types(self) -> None:
        for event_type in DomainEventType:
            event = DomainEvent.create(event_type, "id-1", "aggregate")
            restored = DomainEvent.from_json(event.to_json())
            assert restored.event_type == event_type

    def test_roundtrip_with_empty_data(self) -> None:
        event = DomainEvent.create(DomainEventType.USER_SIGNED_IN, "u-1", "user")
        restored = DomainEvent.from_json(event.to_json())
        assert restored.data == {}
        assert restored.metadata == {}
