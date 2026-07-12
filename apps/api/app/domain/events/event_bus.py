from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Self

logger = logging.getLogger(__name__)

REDIS_CHANNEL = "astra:events"
INSTANCE_ID = os.getpid()


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DomainEventType(Enum):
    # Campaign events
    CAMPAIGN_CREATED = "campaign.created"
    CAMPAIGN_UPDATED = "campaign.updated"
    CAMPAIGN_ACTIVATED = "campaign.activated"
    CAMPAIGN_PAUSED = "campaign.paused"
    CAMPAIGN_COMPLETED = "campaign.completed"
    CAMPAIGN_ARCHIVED = "campaign.archived"

    # Content events
    CONTENT_CREATED = "content.created"
    CONTENT_UPDATED = "content.updated"
    CONTENT_APPROVED = "content.approved"
    CONTENT_PUBLISHED = "content.published"
    CONTENT_SCHEDULED = "content.scheduled"
    CONTENT_REJECTED = "content.rejected"

    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"

    # Analytics events
    REPORT_GENERATED = "report.generated"
    REPORT_SCHEDULED = "report.scheduled"
    ANALYTICS_REFRESHED = "analytics.refreshed"

    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"

    # System events
    USER_SIGNED_IN = "user.signed_in"
    USER_SIGNED_UP = "user.signed_up"
    USER_UPDATED = "user.updated"
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"

    # AI events
    AI_CONTENT_GENERATED = "ai.content_generated"
    AI_AGENT_TASK_COMPLETED = "ai.agent_task_completed"
    AI_AGENT_TASK_FAILED = "ai.agent_task_failed"

    # Advertising events
    AD_CAMPAIGN_SYNCED = "ad.campaign_synced"
    AD_INSIGHTS_REFRESHED = "ad.insights_refreshed"
    AD_ACCOUNT_CONNECTED = "ad.account_connected"

    # Billing events
    BILLING_PLAN_CHANGED = "billing.plan_changed"
    BILLING_USAGE_EXCEEDED = "billing.usage_exceeded"
    BILLING_PAYMENT_FAILED = "billing.payment_failed"

    # Email events
    EMAIL_CAMPAIGN_SENT = "email.campaign_sent"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_OPENED = "email.opened"
    EMAIL_CLICKED = "email.clicked"


@dataclass
class DomainEvent:
    event_type: DomainEventType
    aggregate_id: str
    aggregate_type: str
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    version: int = 1
    correlation_id: str | None = None
    causation_id: str | None = None
    priority: EventPriority = EventPriority.NORMAL
    source_instance: str = field(default_factory=lambda: INSTANCE_ID)

    @classmethod
    def create(
        cls,
        event_type: DomainEventType,
        aggregate_id: str,
        aggregate_type: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> DomainEvent:
        return cls(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=data or {},
            metadata=metadata or {},
            correlation_id=correlation_id,
            priority=priority,
        )

    def to_json(self) -> str:
        payload = {
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "data": self.data,
            "metadata": self.metadata,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "priority": self.priority.value,
            "source_instance": self.source_instance,
        }
        return json.dumps(payload)

    @classmethod
    def from_json(cls, raw: str) -> DomainEvent:
        payload = json.loads(raw)
        return cls(
            event_type=DomainEventType(payload["event_type"]),
            aggregate_id=payload["aggregate_id"],
            aggregate_type=payload["aggregate_type"],
            data=payload.get("data", {}),
            metadata=payload.get("metadata", {}),
            event_id=payload.get("event_id", str(uuid.uuid4())),
            timestamp=payload.get("timestamp", time.time()),
            version=payload.get("version", 1),
            correlation_id=payload.get("correlation_id"),
            causation_id=payload.get("causation_id"),
            priority=EventPriority(payload.get("priority", EventPriority.NORMAL.value)),
            source_instance=payload.get("source_instance", "unknown"),
        )


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    _instance: ClassVar[EventBus | None] = None
    _subscribers: ClassVar[dict[DomainEventType, list[EventHandler]]] = {}
    _global_subscribers: ClassVar[list[EventHandler]] = []
    _history: ClassVar[deque[DomainEvent]] = deque(maxlen=1000)
    _redis_client: ClassVar[Any | None] = None
    _pubsub: ClassVar[Any | None] = None
    _listener_task: ClassVar[asyncio.Task[None] | None] = None
    _redis_enabled: ClassVar[bool] = False

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        if cls._listener_task and not cls._listener_task.done():
            cls._listener_task.cancel()
        cls._instance = None
        cls._subscribers.clear()
        cls._global_subscribers.clear()
        cls._history.clear()
        cls._redis_client = None
        cls._pubsub = None
        cls._listener_task = None
        cls._redis_enabled = False

    @classmethod
    async def enable_redis(cls, redis_url: str) -> None:
        try:
            from redis.asyncio import Redis

            cls._redis_client = Redis.from_url(redis_url, decode_responses=True)
            await cls._redis_client.ping()
            cls._redis_enabled = True
            cls._pubsub = cls._redis_client.pubsub()
            await cls._pubsub.subscribe(REDIS_CHANNEL)
            cls._listener_task = asyncio.create_task(cls._listen_redis())
            logger.info("EventBus: Redis Pub/Sub enabled on channel '%s'", REDIS_CHANNEL)
        except Exception:
            logger.warning("EventBus: Redis unavailable, falling back to in-memory only")
            cls._redis_enabled = False

    @classmethod
    async def disable_redis(cls) -> None:
        if cls._listener_task and not cls._listener_task.done():
            cls._listener_task.cancel()
        if cls._pubsub:
            await cls._pubsub.unsubscribe(REDIS_CHANNEL)
            await cls._pubsub.close()
        if cls._redis_client:
            await cls._redis_client.close()
        cls._redis_client = None
        cls._pubsub = None
        cls._listener_task = None
        cls._redis_enabled = False

    @classmethod
    async def _listen_redis(cls) -> None:
        try:
            while cls._redis_enabled and cls._pubsub:
                message = await cls._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    try:
                        event = DomainEvent.from_json(message["data"])
                        if event.source_instance == INSTANCE_ID:
                            continue
                        await cls._dispatch_local(event)
                    except Exception:
                        logger.exception("EventBus: failed to process Redis message")
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("EventBus: Redis listener crashed")

    @classmethod
    def subscribe(cls, event_type: DomainEventType, handler: EventHandler) -> Callable[[], None]:
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)

        def unsubscribe() -> None:
            handlers = cls._subscribers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

        return unsubscribe

    @classmethod
    def subscribe_all(cls, handler: EventHandler) -> Callable[[], None]:
        cls._global_subscribers.append(handler)

        def unsubscribe() -> None:
            if handler in cls._global_subscribers:
                cls._global_subscribers.remove(handler)

        return unsubscribe

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        cls._history.append(event)

        await cls._dispatch_local(event)

        if cls._redis_enabled and cls._redis_client:
            try:
                await cls._redis_client.publish(REDIS_CHANNEL, event.to_json())
            except Exception:
                logger.warning(
                    "EventBus: failed to publish event to Redis: %s", event.event_type.value
                )

    @classmethod
    async def _dispatch_local(cls, event: DomainEvent) -> None:
        handlers = list(cls._subscribers.get(event.event_type, []))
        global_handlers = list(cls._global_subscribers)

        all_handlers = handlers + global_handlers
        if not all_handlers:
            logger.debug("No handlers for event: %s", event.event_type.value)
            return

        results = await asyncio.gather(
            *[cls._safe_dispatch(h, event) for h in all_handlers],
            return_exceptions=True,
        )

        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(
                "Event %s had %d handler error(s): %s",
                event.event_type.value,
                len(errors),
                errors[0],
            )

    @classmethod
    async def _safe_dispatch(cls, handler: EventHandler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Handler %s failed for event %s",
                handler.__name__,
                event.event_type.value,
            )
            raise

    @classmethod
    def get_history(
        cls,
        event_type: DomainEventType | None = None,
        limit: int = 50,
    ) -> list[DomainEvent]:
        items = list(cls._history)
        recent = items[-limit:] if len(items) > limit else items
        if event_type:
            return [e for e in recent if e.event_type == event_type]
        return recent

    @classmethod
    def clear_history(cls) -> None:
        cls._history.clear()

    @classmethod
    async def get_redis_info(cls) -> dict[str, Any]:
        if not cls._redis_enabled or not cls._redis_client:
            return {"enabled": False, "connected": False}
        try:
            info = await cls._redis_client.info("stats")
            return {
                "enabled": True,
                "connected": True,
                "channel": REDIS_CHANNEL,
                "messages_published": info.get("pubsub_channels", 0),
            }
        except Exception:
            return {"enabled": True, "connected": False}


def event_handler(event_type: DomainEventType):
    def decorator(func: EventHandler) -> EventHandler:
        EventBus.subscribe(event_type, func)
        return func

    return decorator
