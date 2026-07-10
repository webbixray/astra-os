from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.common import now


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_UPDATE = "task_update"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    QUERY = "query"
    RESPONSE = "response"
    ESCALATION = "escalation"
    STATUS_CHECK = "status_check"


@dataclass
class AgentMessage:
    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.QUERY
    sender_id: UUID = field(default_factory=uuid4)
    receiver_id: UUID | None = None
    task_id: UUID | None = None
    content: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(
        cls,
        type: MessageType,
        sender_id: UUID,
        content: str,
        receiver_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> "AgentMessage":
        return cls(
            type=type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            task_id=task_id,
        )


class MessageBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def subscribe(self, agent_id: str, handler) -> None:
        if agent_id not in self._handlers:
            self._handlers[agent_id] = []
        self._handlers[agent_id].append(handler)

    async def publish(self, message: AgentMessage) -> list:
        results = []
        for handler in self._handlers.get(str(message.receiver_id), []):
            result = await handler(message)
            results.append(result)
        return results

    async def broadcast(self, message: AgentMessage) -> list:
        results = []
        for handlers in self._handlers.values():
            for handler in handlers:
                result = await handler(message)
                results.append(result)
        return results
