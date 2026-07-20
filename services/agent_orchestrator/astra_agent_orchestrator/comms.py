"""Redis-backed inter-agent communication and audit trail.

This module provides:
- RedisMessageBus: Redis Pub/Sub message bus for agent-to-agent communication
- AgentAuditTrail: Persistent reasoning trace storage
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import redis.asyncio as redis

from .agent import AgentMessage, AgentResult

logger = logging.getLogger(__name__)


class RedisMessageBus:
    """Redis Pub/Sub backed message bus for inter-agent communication.

    Each agent subscribes to a channel `agent:{agent_id}`. Messages are
    published as JSON envelopes. Supports topic-based pub/sub and
    request/response patterns via correlation IDs.
    """

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._pubsub: redis.client.PubSub | None = None
        self._subscriptions: dict[str, list[asyncio.Queue[AgentMessage]]] = {}
        self._listen_task: asyncio.Task | None = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the message bus listener."""
        if self._running:
            return
        self._running = True
        self._pubsub = self._redis.pubsub()
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Redis message bus started")

    async def stop(self) -> None:
        """Stop the message bus listener."""
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        logger.info("Redis message bus stopped")

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to an agent via Redis Pub/Sub."""
        channel = f"agent:{message.to_agent}"
        envelope = {
            "message_id": str(message.message_id)
            if hasattr(message, "message_id")
            else str(uuid4()),
            "from_agent": str(message.from_agent),
            "to_agent": str(message.to_agent),
            "message_type": message.message_type,
            "payload": message.payload,
            "correlation_id": str(message.correlation_id) if message.correlation_id else None,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        try:
            await self._redis.publish(channel, json.dumps(envelope, default=str))
            logger.debug("Published message to %s: %s", channel, message.message_type)
            return True
        except Exception:
            logger.exception("Failed to publish message to %s", channel)
            return False

    async def receive_message(
        self, agent_id: UUID, timeout: float | None = None
    ) -> AgentMessage | None:
        """Receive a message for an agent (waits on local queue)."""
        channel = f"agent:{agent_id}"
        async with self._lock:
            if channel not in self._subscriptions:
                self._subscriptions[channel] = []
            queue: asyncio.Queue[AgentMessage] = asyncio.Queue()
            self._subscriptions[channel].append(queue)

            # Ensure we're subscribed to the Redis channel
            if self._pubsub and channel not in [
                s.decode() for s in (await self._pubsub.channels()) or []
            ]:
                await self._pubsub.subscribe(channel)

        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            return await queue.get()
        except TimeoutError:
            return None
        finally:
            async with self._lock:
                if channel in self._subscriptions:
                    try:
                        self._subscriptions[channel].remove(queue)
                    except ValueError:
                        pass

    async def broadcast(self, message: AgentMessage, agent_ids: list[UUID]) -> int:
        """Broadcast message to multiple agents."""
        sent = 0
        for agent_id in agent_ids:
            broadcast_msg = AgentMessage(
                from_agent=message.from_agent,
                to_agent=agent_id,
                message_type=message.message_type,
                payload=message.payload,
                correlation_id=message.correlation_id,
            )
            if await self.send_message(broadcast_msg):
                sent += 1
        return sent

    async def _listen_loop(self) -> None:
        """Background loop that dispatches Redis messages to local queues."""
        while self._running:
            try:
                if not self._pubsub:
                    await asyncio.sleep(0.1)
                    continue

                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=0.1
                )
                if message and message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()

                    try:
                        envelope = json.loads(message["data"])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning("Invalid message envelope on %s", channel)
                        continue

                    agent_msg = AgentMessage(
                        from_agent=UUID(envelope["from_agent"]),
                        to_agent=UUID(envelope["to_agent"]),
                        message_type=envelope["message_type"],
                        payload=envelope.get("payload", {}),
                        correlation_id=(
                            UUID(envelope["correlation_id"])
                            if envelope.get("correlation_id")
                            else None
                        ),
                    )

                    # Dispatch to local queues
                    async with self._lock:
                        queues = self._subscriptions.get(channel, [])
                    for q in queues:
                        await q.put(agent_msg)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in message bus listen loop")
                await asyncio.sleep(0.1)


@dataclass
class AgentTraceEntry:
    """A single reasoning trace entry for audit."""

    trace_id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    task_id: UUID | None = None
    parent_trace_id: UUID | None = None
    agent_type: str = ""
    agent_name: str = ""
    iteration: int = 0
    thought: str | None = None
    action: str | None = None
    action_input: dict[str, Any] | None = None
    observation: str | None = None
    final_answer: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int | None = None
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentAuditTrail:
    """Persistent audit trail for agent reasoning traces.

    Stores every step of the ReAct loop: thought → action → observation.
    Enables full replay, debugging, and compliance reporting.
    """

    def __init__(self, pg_pool: asyncpg.Pool | None = None):
        self._pg_pool = pg_pool
        self._buffer: list[AgentTraceEntry] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_interval = 5.0  # seconds
        self._flush_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background flush task."""
        if self._pg_pool:
            self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stop the background flush and flush remaining entries."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()

    async def record(self, entry: AgentTraceEntry) -> None:
        """Record a trace entry (buffered, flushed periodically)."""
        async with self._buffer_lock:
            self._buffer.append(entry)

        if len(self._buffer) >= 50:
            await self.flush()

    async def record_step(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        agent_type: str,
        agent_name: str,
        iteration: int,
        thought: str | None = None,
        action: str | None = None,
        action_input: dict[str, Any] | None = None,
        observation: str | None = None,
        task_id: UUID | None = None,
    ) -> AgentTraceEntry:
        """Convenience method to record a single ReAct step."""
        entry = AgentTraceEntry(
            agent_id=agent_id,
            tenant_id=tenant_id,
            agent_type=agent_type,
            agent_name=agent_name,
            iteration=iteration,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation,
            task_id=task_id,
        )
        await self.record(entry)
        return entry

    async def record_completion(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        agent_type: str,
        agent_name: str,
        result: AgentResult,
        task_id: UUID | None = None,
    ) -> AgentTraceEntry:
        """Record the final result of an agent execution."""
        entry = AgentTraceEntry(
            agent_id=agent_id,
            tenant_id=tenant_id,
            agent_type=agent_type,
            agent_name=agent_name,
            iteration=result.iterations if hasattr(result, "iterations") else 0,
            final_answer=result.output if hasattr(result, "output") else None,
            tool_calls=[
                tc.__dict__ if hasattr(tc, "__dict__") else str(tc)
                for tc in (result.tool_calls if hasattr(result, "tool_calls") else [])
            ],
            tool_results=[
                tr.__dict__ if hasattr(tr, "__dict__") else str(tr)
                for tr in (result.tool_results if hasattr(result, "tool_results") else [])
            ],
            tokens_used=result.tokens_used if hasattr(result, "tokens_used") else 0,
            cost_usd=result.cost_usd if hasattr(result, "cost_usd") else 0.0,
            duration_ms=result.duration_ms if hasattr(result, "duration_ms") else None,
            success=result.success if hasattr(result, "success") else True,
            error=result.error if hasattr(result, "error") else None,
            task_id=task_id,
        )
        await self.record(entry)
        return entry

    async def flush(self) -> int:
        """Flush buffered entries to PostgreSQL."""
        async with self._buffer_lock:
            if not self._buffer:
                return 0
            entries = list(self._buffer)
            self._buffer.clear()

        if not self._pg_pool:
            return len(entries)

        try:
            async with self._pg_pool.acquire() as conn:
                await conn.executemany(
                    """
                    INSERT INTO agent_traces (
                        trace_id, agent_id, tenant_id, task_id, parent_trace_id,
                        agent_type, agent_name, iteration, thought, action,
                        action_input, observation, final_answer, tool_calls,
                        tool_results, tokens_used, cost_usd, duration_ms,
                        success, error, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                    )
                    """,
                    [
                        (
                            e.trace_id,
                            e.agent_id,
                            e.tenant_id,
                            e.task_id,
                            e.parent_trace_id,
                            e.agent_type,
                            e.agent_name,
                            e.iteration,
                            e.thought,
                            e.action,
                            json.dumps(e.action_input) if e.action_input else None,
                            e.observation,
                            e.final_answer,
                            json.dumps(e.tool_calls, default=str),
                            json.dumps(e.tool_results, default=str),
                            e.tokens_used,
                            e.cost_usd,
                            e.duration_ms,
                            e.success,
                            e.error,
                            json.dumps(e.metadata, default=str),
                        )
                        for e in entries
                    ],
                )
            logger.debug("Flushed %d trace entries to PostgreSQL", len(entries))
            return len(entries)
        except Exception:
            logger.exception("Failed to flush trace entries")
            # Re-buffer on failure
            async with self._buffer_lock:
                self._buffer.extend(entries)
            return 0

    async def _flush_loop(self) -> None:
        """Background loop to periodically flush buffered entries."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in trace flush loop")

    async def query_traces(
        self,
        tenant_id: UUID | None = None,
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AgentTraceEntry]:
        """Query traces from PostgreSQL."""
        if not self._pg_pool:
            return []

        conditions = []
        params: list[Any] = []

        if tenant_id:
            conditions.append(f"tenant_id = ${len(params) + 1}")
            params.append(tenant_id)
        if agent_id:
            conditions.append(f"agent_id = ${len(params) + 1}")
            params.append(agent_id)
        if task_id:
            conditions.append(f"task_id = ${len(params) + 1}")
            params.append(task_id)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM agent_traces
                {where}
                ORDER BY created_at DESC
                LIMIT ${len(params)}
                """,
                *params,
            )

        return [
            AgentTraceEntry(
                trace_id=row["trace_id"],
                agent_id=row["agent_id"],
                tenant_id=row["tenant_id"],
                task_id=row.get("task_id"),
                parent_trace_id=row.get("parent_trace_id"),
                agent_type=row["agent_type"],
                agent_name=row["agent_name"],
                iteration=row["iteration"],
                thought=row.get("thought"),
                action=row.get("action"),
                action_input=json.loads(row["action_input"]) if row.get("action_input") else None,
                observation=row.get("observation"),
                final_answer=row.get("final_answer"),
                tool_calls=json.loads(row["tool_calls"]) if row.get("tool_calls") else [],
                tool_results=json.loads(row["tool_results"]) if row.get("tool_results") else [],
                tokens_used=row["tokens_used"],
                cost_usd=row["cost_usd"],
                duration_ms=row.get("duration_ms"),
                success=row["success"],
                error=row.get("error"),
                metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                created_at=row["created_at"],
            )
            for row in rows
        ]


# ---------------------------------------------------------------------------
# Global instances
# ---------------------------------------------------------------------------
_redis_message_bus: RedisMessageBus | None = None
_agent_audit_trail: AgentAuditTrail | None = None


async def get_redis_message_bus(redis_url: str | None = None) -> RedisMessageBus:
    """Get or create the global Redis message bus."""
    global _redis_message_bus
    if _redis_message_bus is None:
        url = redis_url or "redis://localhost:6379/0"
        client = redis.from_url(url)
        _redis_message_bus = RedisMessageBus(client)
        await _redis_message_bus.start()
    return _redis_message_bus


def get_agent_audit_trail(pg_pool: asyncpg.Pool | None = None) -> AgentAuditTrail:
    """Get or create the global agent audit trail."""
    global _agent_audit_trail
    if _agent_audit_trail is None:
        _agent_audit_trail = AgentAuditTrail(pg_pool=pg_pool)
    return _agent_audit_trail
