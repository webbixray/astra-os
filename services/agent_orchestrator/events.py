"""Event bus for agent system."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """An event in the system."""

    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    source: UUID | str = ""
    tenant_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID | None = None


class EventBus:
    """Event bus for inter-component communication."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)
        self._wildcard_subscribers: list[Callable[[Event], Any]] = []
        self._lock = asyncio.Lock()
        self._event_history: list[Event] = []
        self._max_history = 10000

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
    ) -> Callable[[], None]:
        """Subscribe to an event type."""
        async with self._lock:
            self._subscribers[event_type].append(handler)

        def unsubscribe():
            asyncio.create_task(self.unsubscribe(event_type, handler))

        return unsubscribe

    async def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
    ) -> None:
        """Unsubscribe from an event type."""
        async with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    async def subscribe_all(self, handler: Callable[[Event], Any]) -> Callable[[], None]:
        """Subscribe to all events."""
        async with self._lock:
            self._wildcard_subscribers.append(handler)

        def unsubscribe():
            asyncio.create_task(self.unsubscribe_all(handler))

        return unsubscribe

    async def unsubscribe_all(self, handler: Callable[[Event], Any]) -> None:
        """Unsubscribe from all events."""
        async with self._lock:
            if handler in self._wildcard_subscribers:
                self._wildcard_subscribers.remove(handler)

    async def publish(self, event: Event) -> int:
        """Publish an event to all subscribers."""
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Notify subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        wildcard = self._wildcard_subscribers

        all_handlers = subscribers + wildcard
        if not all_handlers:
            return 0

        # Run handlers concurrently
        tasks = []
        for handler in all_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    tasks.append(asyncio.to_thread(handler, event))
            except Exception as e:
                logger.exception("Error creating handler task: %s", e)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return len(all_handlers)

    async def publish_sync(self, event: Event) -> int:
        """Publish event synchronously (wait for all handlers)."""
        return await self.publish(event)

    def get_history(
        self,
        event_type: str | None = None,
        source: UUID | str | None = None,
        tenant_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get event history with filters."""
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if str(e.source) == str(source)]
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]

        return events[-limit:]

    async def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


class EventStore:
    """Persistent event store using PostgreSQL."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def append(self, event: Event) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (event_id, event_type, source, tenant_id, payload, metadata, timestamp, correlation_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                event.event_id,
                event.event_type,
                str(event.source),
                event.tenant_id,
                json.dumps(event.payload),
                json.dumps(event.metadata),
                event.timestamp,
                event.correlation_id,
            )

    async def get_events(
        self,
        event_type: str | None = None,
        source: UUID | None = None,
        tenant_id: UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Event]:
        conditions = []
        params: list[Any] = []

        if event_type:
            conditions.append(f"event_type = ${len(params) + 1}")
            params.append(event_type)

        if source:
            conditions.append(f"source = ${len(params) + 1}")
            params.append(str(source))

        if tenant_id:
            conditions.append(f"tenant_id = ${len(params) + 1}")
            params.append(tenant_id)

        if start_time:
            conditions.append(f"timestamp >= ${len(params) + 1}")
            params.append(start_time)

        if end_time:
            conditions.append(f"timestamp <= ${len(params) + 1}")
            params.append(end_time)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT event_id, event_type, source, tenant_id, payload, metadata, timestamp, correlation_id
            FROM events
            {where}
            ORDER BY timestamp DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([100, 0])  # default limit/offset

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        events = []
        for row in rows:
            events.append(Event(
                event_id=row["event_id"],
                event_type=row["event_type"],
                source=UUID(row["source"]),
                tenant_id=row["tenant_id"],
                payload=json.loads(row["payload"]),
                metadata=json.loads(row["metadata"]),
                timestamp=row["timestamp"],
                correlation_id=row["correlation_id"],
            ))

        return events


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus