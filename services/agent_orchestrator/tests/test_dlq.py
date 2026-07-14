"""Tests for Dead Letter Queue."""

import json
from unittest.mock import AsyncMock

import pytest
from services.agent_orchestrator.dlq import (
    DeadLetter,
    DeadLetterQueue,
    DLQConsumer,
)


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue."""

    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def dlq(self, mock_redis):
        return DeadLetterQueue(mock_redis, "test:dlq")

    @pytest.mark.asyncio
    async def test_add_creates_dead_letter(self, dlq, mock_redis):
        """add() should create dead letter and add to stream."""
        mock_redis.xadd.return_value = "123-0"

        dlq_id = await dlq.add(
            original_stream="test:stream",
            message_id="456-0",
            payload={"task": "test"},
            error="Something failed",
            retry_count=3,
            consumer_group="group1",
            consumer_name="consumer1",
        )

        assert dlq_id == "123-0"
        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "test:dlq"
        data = json.loads(call_args[0][1]["data"])
        assert data["original_stream"] == "test:stream"
        assert data["error"] == "Something failed"
        assert data["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_get_pending_count(self, dlq, mock_redis):
        """get_pending_count should return stream length."""
        mock_redis.xinfo_stream.return_value = {"length": 42}

        count = await dlq.get_pending_count()

        assert count == 42

    @pytest.mark.asyncio
    async def test_get_pending_count_stream_not_exists(self, dlq, mock_redis):
        """get_pending_count should return 0 if stream doesn't exist."""
        from redis import ResponseError
        mock_redis.xinfo_stream.side_effect = ResponseError("no such key")

        count = await dlq.get_pending_count()

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_recent(self, dlq, mock_redis):
        """get_recent should return parsed dead letters."""
        dead_letter = DeadLetter(
            id="dlq-1",
            original_stream="test:stream",
            original_message_id="msg-1",
            payload={"task": "test"},
            error="Failed",
            retry_count=3,
            failed_at=time.time(),
            consumer_group="group1",
            consumer_name="consumer1",
        )

        mock_redis.xrevrange.return_value = [
            ("dlq-1", {"data": json.dumps(asdict(dead_letter))}),
        ]

        result = await dlq.get_recent(count=10)

        assert len(result) == 1
        assert result[0].original_stream == "test:stream"

    @pytest.mark.asyncio
    async def test_replay(self, dlq, mock_redis):
        """Replay should re-add to target stream and delete from DLQ."""
        dead_letter = DeadLetter(
            id="dlq-1",
            original_stream="test:stream",
            original_message_id="msg-1",
            payload={"task": "test"},
            error="Failed",
            retry_count=3,
            failed_at=time.time(),
            consumer_group="group1",
            consumer_name="consumer1",
        )

        mock_redis.xrange.return_value = [
            ("dlq-1", {"data": json.dumps(asdict(dead_letter))}),
        ]
        mock_redis.xadd.return_value = "new-msg-id"

        result = await dlq.replay("dlq-1")

        assert result is True
        mock_redis.xadd.assert_called_with("test:stream", {"data": json.dumps({"task": "test"})})
        mock_redis.xdel.assert_called_with("test:dlq", "dlq-1")

    @pytest.mark.asyncio
    async def test_replay_not_found(self, dlq, mock_redis):
        """Replay should return False if message not found."""
        mock_redis.xrange.return_value = []

        result = await dlq.replay("nonexistent")

        assert result is False


class TestDLQConsumer:
    """Tests for DLQConsumer."""

    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def handler(self):
        return AsyncMock()

    @pytest.fixture
    def consumer(self, mock_redis, handler):
        dlq = DeadLetterQueue(mock_redis)
        return DLQConsumer(
            redis_client=mock_redis,
            stream="test:stream",
            group_name="test-group",
            consumer_name="consumer-1",
            handler=handler,
            max_retries=2,
            dlq=dlq,
        )

    @pytest.mark.asyncio
    async def test_start_creates_consumer_group(self, consumer, mock_redis):
        """start() should create consumer group."""
        await consumer.start()

        mock_redis.xgroup_create.assert_called_with(
            "test:stream", "test-group", id="0", mkstream=True
        )

    @pytest.mark.asyncio
    async def test_start_handles_busygroup(self, consumer, mock_redis):
        """start() should handle BUSYGROUP error gracefully."""
        from redis import ResponseError
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")

        await consumer.start()  # Should not raise

    @pytest.mark.asyncio
    async def test_process_message_success(self, consumer, mock_redis):
        """Successful message processing should ack."""
        msg_id = "123-0"
        data = {"task": "test"}

        await consumer._process_message(msg_id, data)

        mock_redis.xack.assert_called_with("test:stream", "test-group", msg_id)

    @pytest.mark.asyncio
    async def test_process_message_retry_then_success(self, consumer, mock_redis):
        """Failed message should retry and eventually succeed."""
        mock_redis.xreadgroup.return_value = None

        # First two calls fail, third succeeds
        consumer.handler.side_effect = [
            RuntimeError("fail 1"),
            RuntimeError("fail 2"),
            None,  # success
        ]

        msg_id = "123-0"
        data = {"task": "test"}

        await consumer._process_message(msg_id, data)

        # Should have been re-added to stream twice with retry_count
        assert mock_redis.xadd.call_count == 2
        # Final ack
        mock_redis.xack.assert_called_with("test:stream", "test-group", msg_id)

    @pytest.mark.asyncio
    async def test_process_message_max_retries_to_dlq(self, consumer, mock_redis):
        """Message exceeding max retries should go to DLQ."""
        consumer.max_retries = 2
        mock_redis.xreadgroup.return_value = None

        # All calls fail
        consumer.handler.side_effect = RuntimeError("always fails")

        msg_id = "123-0"
        data = {"task": "test"}

        await consumer._process_message(msg_id, data)

        # Should be added to DLQ
        assert consumer.dlq.add.call_count == 1
        call_args = consumer.dlq.add.call_args
        assert call_args[1]["retry_count"] == 3  # max_retries + 1
        assert call_args[1]["error"] == "always fails"

        # Should ack to remove from pending
        mock_redis.xack.assert_called_with("test:stream", "test-group", msg_id)


class TestDeadLetter:
    """Tests for DeadLetter dataclass."""

    def test_dead_letter_creation(self):
        """DeadLetter should be creatable with all fields."""
        dl = DeadLetter(
            id="test-1",
            original_stream="stream1",
            original_message_id="msg-1",
            payload={"key": "value"},
            error="Test error",
            retry_count=3,
            failed_at=1234567890.0,
            consumer_group="group1",
            consumer_name="consumer1",
        )

        assert dl.id == "test-1"
        assert dl.payload == {"key": "value"}
        assert dl.retry_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
