"""Tests for the event bus."""

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from services.agent_orchestrator.events import Event, EventBus


class TestEvent:
    """Tests for Event dataclass."""

    def test_create_event(self) -> None:
        event = Event(
            event_type="test.event",
            source=uuid.uuid4(),
            payload={"key": "value"},
        )
        assert event.event_type == "test.event"
        assert event.payload == {"key": "value"}
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_with_tenant(self) -> None:
        tenant_id = uuid.uuid4()
        event = Event(
            event_type="test.event",
            source="test",
            tenant_id=tenant_id,
        )
        assert event.tenant_id == tenant_id


class TestEventBus:
    """Tests for EventBus."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self) -> None:
        bus = EventBus()
        received = []

        async def handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe("test.event", handler)
        event = Event(event_type="test.event", source="test")
        count = await bus.publish(event)

        assert count == 1
        assert len(received) == 1
        assert received[0].event_type == "test.event"

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        bus = EventBus()
        received = []

        async def handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe("test.event", handler)
        await bus.unsubscribe("test.event", handler)
        event = Event(event_type="test.event", source="test")
        count = await bus.publish(event)

        assert count == 0
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_wildcard_subscribe(self) -> None:
        bus = EventBus()
        received = []

        async def handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe_all(handler)
        event = Event(event_type="any.event", source="test")
        count = await bus.publish(event)

        assert count == 1
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        received1 = []
        received2 = []

        async def handler1(event: Event) -> None:
            received1.append(event)

        async def handler2(event: Event) -> None:
            received2.append(event)

        await bus.subscribe("test.event", handler1)
        await bus.subscribe("test.event", handler2)
        event = Event(event_type="test.event", source="test")
        count = await bus.publish(event)

        assert count == 2
        assert len(received1) == 1
        assert len(received2) == 1

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self) -> None:
        bus = EventBus()
        event = Event(event_type="test.event", source="test")
        count = await bus.publish(event)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_handler(self) -> None:
        bus = EventBus()
        received = []

        def sync_handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe("test.event", sync_handler)
        event = Event(event_type="test.event", source="test")
        await bus.publish(event)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash(self) -> None:
        bus = EventBus()

        async def bad_handler(event: Event) -> None:
            raise RuntimeError("handler error")

        received = []

        async def good_handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe("test.event", bad_handler)
        await bus.subscribe("test.event", good_handler)
        event = Event(event_type="test.event", source="test")
        count = await bus.publish(event)

        # Both handlers should have been invoked
        assert count == 2
        # Good handler should still receive the event
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_event_history(self) -> None:
        bus = EventBus()
        event1 = Event(event_type="type.a", source="test")
        event2 = Event(event_type="type.b", source="test")
        await bus.publish(event1)
        await bus.publish(event2)

        history = bus.get_history()
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_event_history_filter_type(self) -> None:
        bus = EventBus()
        await bus.publish(Event(event_type="type.a", source="test"))
        await bus.publish(Event(event_type="type.b", source="test"))
        await bus.publish(Event(event_type="type.a", source="test"))

        history = bus.get_history(event_type="type.a")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_event_history_limit(self) -> None:
        bus = EventBus()
        for i in range(5):
            await bus.publish(Event(event_type="test", source="test"))

        history = bus.get_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_clear_history(self) -> None:
        bus = EventBus()
        await bus.publish(Event(event_type="test", source="test"))
        assert len(bus.get_history()) == 1
        await bus.clear_history()
        assert len(bus.get_history()) == 0

    @pytest.mark.asyncio
    async def test_max_history_limit(self) -> None:
        bus = EventBus()
        bus._max_history = 3
        for i in range(5):
            await bus.publish(Event(event_type="test", source=str(i)))

        assert len(bus._event_history) == 3

    @pytest.mark.asyncio
    async def test_concurrent_publish(self) -> None:
        bus = EventBus()
        received = []

        async def handler(event: Event) -> None:
            await asyncio.sleep(0.01)
            received.append(event)

        await bus.subscribe("test.event", handler)
        events = [
            Event(event_type="test.event", source=f"src-{i}") for i in range(10)
        ]
        await asyncio.gather(*[bus.publish(e) for e in events])
        assert len(received) == 10
