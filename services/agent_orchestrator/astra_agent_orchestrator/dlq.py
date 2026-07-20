"""Dead Letter Queue for failed async tasks using Redis Streams."""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

import redis.asyncio as redis


@dataclass
class DeadLetter:
    """A failed task that has been moved to the DLQ."""

    id: str
    original_stream: str
    original_message_id: str
    payload: dict[str, Any]
    error: str
    retry_count: int
    failed_at: float
    consumer_group: str
    consumer_name: str


class DeadLetterQueue:
    """Dead Letter Queue using Redis Streams.

    Failed messages from consumer groups are moved here after max retries.
    Provides observability, replay capability, and alerting.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        dlq_stream: str = "astra:dlq",
        max_length: int = 10000,
    ):
        self.redis = redis_client
        self.dlq_stream = dlq_stream
        self.max_length = max_length

    async def add(
        self,
        original_stream: str,
        message_id: str,
        payload: dict[str, Any],
        error: str,
        retry_count: int,
        consumer_group: str,
        consumer_name: str,
    ) -> str:
        """Add a dead letter to the queue.

        Returns:
            The message ID in the DLQ stream.

        """
        dead_letter = DeadLetter(
            id=str(uuid4()),
            original_stream=original_stream,
            original_message_id=message_id,
            payload=payload,
            error=error,
            retry_count=retry_count,
            failed_at=time.time(),
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )

        # Add to stream with MAXLEN to prevent unbounded growth
        dlq_id = await self.redis.xadd(
            self.dlq_stream,
            {"data": json.dumps(asdict(dead_letter))},
            maxlen=self.max_length,
            approximate=True,
        )

        return dlq_id

    async def get_pending_count(self) -> int:
        """Get number of messages in DLQ."""
        try:
            info = await self.redis.xinfo_stream(self.dlq_stream)
            return info["length"]
        except redis.ResponseError:
            # Stream doesn't exist yet
            return 0

    async def get_recent(
        self,
        count: int = 100,
        start: str = "-",
        end: str = "+",
    ) -> list[DeadLetter]:
        """Get recent dead letters (newest first)."""
        messages = await self.redis.xrevrange(
            self.dlq_stream,
            max=end,
            min=start,
            count=count,
        )

        result = []
        for msg_id, data in messages:
            dl_data = json.loads(data["data"])
            dl_data["id"] = msg_id
            result.append(DeadLetter(**dl_data))

        return result

    async def get_by_original_stream(
        self,
        original_stream: str,
        count: int = 100,
    ) -> list[DeadLetter]:
        """Get dead letters from a specific original stream."""
        # We need to scan and filter - not ideal but works for debugging
        all_dl = await self.get_recent(count=count * 10)  # Overscan
        return [dl for dl in all_dl if dl.original_stream == original_stream][:count]

    async def replay(
        self,
        message_id: str,
        target_stream: str | None = None,
    ) -> bool:
        """Replay a dead letter back to its original stream (or target).

        Returns:
            True if replayed successfully, False if not found.

        """
        # Get the message
        messages = await self.redis.xrange(
            self.dlq_stream,
            min=message_id,
            max=message_id,
            count=1,
        )

        if not messages:
            return False

        msg_id, data = messages[0]
        dl_data = json.loads(data["data"])

        # Determine target stream
        stream = target_stream or dl_data["original_stream"]

        # Re-add to original stream (with new message ID)
        await self.redis.xadd(stream, {"data": json.dumps(dl_data["payload"])})

        # Remove from DLQ
        await self.redis.xdel(self.dlq_stream, message_id)

        return True

    async def replay_all(
        self,
        target_stream: str | None = None,
        filter_original_stream: str | None = None,
    ) -> int:
        """Replay all dead letters (or filtered subset).

        Returns:
            Number of messages replayed.

        """
        dead_letters = await self.get_recent(count=10000)

        if filter_original_stream:
            dead_letters = [
                dl for dl in dead_letters
                if dl.original_stream == filter_original_stream
            ]

        count = 0
        for dl in dead_letters:
            stream = target_stream or dl.original_stream
            await self.redis.xadd(stream, {"data": json.dumps(dl.payload)})
            await self.redis.xdel(self.dlq_stream, dl.id)
            count += 1

        return count

    async def delete(self, message_id: str) -> bool:
        """Delete a specific dead letter."""
        result = await self.redis.xdel(self.dlq_stream, message_id)
        return result > 0


class DLQConsumer:
    """Consumer that processes messages with automatic retry and DLQ on max retries.

    Uses Redis Streams consumer groups for exactly-once delivery semantics.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        stream: str,
        group_name: str,
        consumer_name: str,
        handler: callable,
        max_retries: int = 3,
        dlq: DeadLetterQueue | None = None,
        block_ms: int = 5000,
        claim_min_idle_ms: int = 60000,
    ):
        self.redis = redis_client
        self.stream = stream
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.handler = handler
        self.max_retries = max_retries
        self.dlq = dlq or DeadLetterQueue(redis_client)
        self.block_ms = block_ms
        self.claim_min_idle_ms = claim_min_idle_ms
        self._running = False

    async def start(self) -> None:
        """Create consumer group if it doesn't exist."""
        try:
            await self.redis.xgroup_create(
                self.stream,
                self.group_name,
                id="0",  # Read from beginning
                mkstream=True,
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def run(self) -> None:
        """Main consumer loop."""
        self._running = True

        while self._running:
            try:
                # Read new messages
                messages = await self.redis.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream: ">"},
                    count=10,
                    block=self.block_ms,
                )

                for stream, msgs in messages:
                    for msg_id, data in msgs:
                        await self._process_message(msg_id, data)

                # Claim stale messages
                await self._claim_stale_messages()

            except Exception as e:
                # Log but continue running
                print(f"Consumer error: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, msg_id: str, data: dict) -> None:
        """Process a single message with retry logic."""
        retry_count = 0

        # Extract retry count from message if present
        if "retry_count" in data:
            retry_count = int(data["retry_count"])

        while retry_count <= self.max_retries:
            try:
                await self.handler(data)

                # Success - ack and done
                await self.redis.xack(self.stream, self.group_name, msg_id)
                return

            except Exception as e:
                retry_count += 1

                if retry_count > self.max_retries:
                    # Max retries exceeded - send to DLQ
                    if self.dlq:
                        await self.dlq.add(
                            original_stream=self.stream,
                            message_id=msg_id,
                            payload=data,
                            error=str(e),
                            retry_count=retry_count,
                            consumer_group=self.group_name,
                            consumer_name=self.consumer_name,
                        )

                    # Ack to remove from pending (it's in DLQ now)
                    await self.redis.xack(self.stream, self.group_name, msg_id)
                    return

                # Retry - update retry count in stream
                await self.redis.xadd(
                    self.stream,
                    {**data, "retry_count": str(retry_count)},
                )
                await self.redis.xack(self.stream, self.group_name, msg_id)

                # Wait before retry with exponential backoff
                await asyncio.sleep(min(2 ** retry_count, 30))

    async def _claim_stale_messages(self) -> None:
        """Claim messages that have been pending too long."""
        try:
            claimed = await self.redis.xautoclaim(
                self.stream,
                self.group_name,
                self.consumer_name,
                min_idle_time=self.claim_min_idle_ms,
                count=10,
            )

            for msg_id, data in claimed[1]:
                await self._process_message(msg_id, data)

        except redis.ResponseError:
            # No pending messages or other issue
            pass

    def stop(self) -> None:
        """Stop the consumer loop."""
        self._running = False


async def create_dlq_consumer(
    redis_client: redis.Redis,
    stream: str,
    group_name: str,
    consumer_name: str,
    handler: callable,
    max_retries: int = 3,
    dlq_stream: str = "astra:dlq",
) -> DLQConsumer:
    """Factory function to create a DLQ consumer with default DLQ."""
    dlq = DeadLetterQueue(redis_client, dlq_stream)
    consumer = DLQConsumer(
        redis_client=redis_client,
        stream=stream,
        group_name=group_name,
        consumer_name=consumer_name,
        handler=handler,
        max_retries=max_retries,
        dlq=dlq,
    )
    await consumer.start()
    return consumer
