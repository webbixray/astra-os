from uuid import uuid4

import pytest

from app.domain.entities.agents.agent import Agent, AgentRole, AgentStatus
from app.domain.entities.agents.communication import AgentMessage, MessageBus, MessageType
from app.domain.entities.agents.task import AgentTask, TaskPriority, TaskStatus


class TestAgent:
    def test_create_agent(self):
        a = Agent.create(
            name="ContentBot",
            role=AgentRole.CONTENT_DIRECTOR,
            capabilities=["write", "edit", "seo"],
            parent_id=uuid4(),
        )
        assert a.name == "ContentBot"
        assert a.role == AgentRole.CONTENT_DIRECTOR
        assert a.capabilities == ["write", "edit", "seo"]
        assert a.parent_id is not None
        assert a.status == AgentStatus.IDLE

    def test_capabilities_defaults_to_empty(self):
        a = Agent.create(name="X", role=AgentRole.SPECIALIST)
        assert a.capabilities == []

    def test_set_status_updates_timestamp(self):
        a = Agent.create(name="X", role=AgentRole.SPECIALIST)
        old_updated = a.updated_at
        a.set_status(AgentStatus.PROCESSING)
        assert a.status == AgentStatus.PROCESSING
        assert a.updated_at >= old_updated

    def test_all_roles_defined(self):
        assert AgentRole.CEO == "ceo"
        assert AgentRole.CAMPAIGN_DIRECTOR == "campaign_director"
        assert AgentRole.CONTENT_DIRECTOR == "content_director"
        assert AgentRole.ANALYTICS_DIRECTOR == "analytics_director"
        assert AgentRole.WORKFLOW_DIRECTOR == "workflow_director"
        assert AgentRole.SPECIALIST == "specialist"

    def test_all_statuses_defined(self):
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.PROCESSING == "processing"
        assert AgentStatus.WAITING == "waiting"
        assert AgentStatus.ERROR == "error"


class TestAgentTask:
    def test_create_task(self):
        t = AgentTask.create(
            title="Write blog post",
            description="Write about AI",
            assigned_by=uuid4(),
            priority=TaskPriority.HIGH,
            parent_task_id=uuid4(),
        )
        assert t.title == "Write blog post"
        assert t.description == "Write about AI"
        assert t.status == TaskStatus.PENDING
        assert t.priority == TaskPriority.HIGH
        assert t.parent_task_id is not None
        assert t.result == {}
        assert t.error is None

    def test_assign_sets_assigned_and_status(self):
        t = AgentTask.create(title="X", description="Y", assigned_by=uuid4())
        agent_id = uuid4()
        t.assign(agent_id)
        assert t.assigned_to == agent_id
        assert t.status == TaskStatus.ASSIGNED

    def test_start_sets_in_progress(self):
        t = AgentTask.create(title="X", description="Y", assigned_by=uuid4())
        t.start()
        assert t.status == TaskStatus.IN_PROGRESS

    def test_complete_sets_completed(self):
        t = AgentTask.create(title="X", description="Y", assigned_by=uuid4())
        t.complete({"words": 500})
        assert t.status == TaskStatus.COMPLETED
        assert t.result == {"words": 500}

    def test_complete_with_none_preserves_result(self):
        t = AgentTask.create(title="X", description="Y", assigned_by=uuid4())
        t.result = {"old": "data"}
        t.complete(None)
        assert t.status == TaskStatus.COMPLETED
        assert t.result == {"old": "data"}

    def test_fail_sets_failed_and_error(self):
        t = AgentTask.create(title="X", description="Y", assigned_by=uuid4())
        t.fail("timeout")
        assert t.status == TaskStatus.FAILED
        assert t.error == "timeout"

    def test_all_statuses(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.ASSIGNED == "assigned"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.BLOCKED == "blocked"

    def test_all_priorities(self):
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.CRITICAL == "critical"


class TestAgentMessage:
    def test_create_message(self):
        sender = uuid4()
        receiver = uuid4()
        task = uuid4()
        m = AgentMessage.create(
            type=MessageType.TASK_ASSIGNMENT,
            sender_id=sender,
            content="Do this task",
            receiver_id=receiver,
            task_id=task,
        )
        assert m.type == MessageType.TASK_ASSIGNMENT
        assert m.sender_id == sender
        assert m.receiver_id == receiver
        assert m.task_id == task
        assert m.content == "Do this task"
        assert m.metadata == {}

    def test_defaults(self):
        m = AgentMessage.create(
            type=MessageType.QUERY,
            sender_id=uuid4(),
            content="Hello",
        )
        assert m.type == MessageType.QUERY
        assert m.receiver_id is None
        assert m.task_id is None


class TestMessageBus:
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        bus = MessageBus()
        results = []

        async def handler(msg):
            results.append(msg.content)

        receiver_id = uuid4()
        bus.subscribe(str(receiver_id), handler)
        msg = AgentMessage.create(
            type=MessageType.QUERY,
            sender_id=uuid4(),
            content="ping",
            receiver_id=receiver_id,
        )
        await bus.publish(msg)
        assert results == ["ping"]

    @pytest.mark.asyncio
    async def test_publish_only_delivers_to_receiver(self):
        bus = MessageBus()
        results_1 = []
        results_2 = []

        async def h1(msg):
            results_1.append(msg.content)

        async def h2(msg):
            results_2.append(msg.content)

        receiver_1 = uuid4()
        receiver_2 = uuid4()
        bus.subscribe(str(receiver_1), h1)
        bus.subscribe(str(receiver_2), h2)

        msg = AgentMessage.create(
            type=MessageType.QUERY,
            sender_id=uuid4(),
            content="for agent 1",
            receiver_id=receiver_1,
        )
        await bus.publish(msg)
        assert results_1 == ["for agent 1"]
        assert results_2 == []

    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_all(self):
        bus = MessageBus()
        all_results = []

        async def h1(msg):
            all_results.append(("1", msg.content))

        async def h2(msg):
            all_results.append(("2", msg.content))

        bus.subscribe("agent-1", h1)
        bus.subscribe("agent-2", h2)

        msg = AgentMessage.create(
            type=MessageType.STATUS_CHECK,
            sender_id=uuid4(),
            content="status?",
        )
        await bus.broadcast(msg)
        assert len(all_results) == 2
        assert {c for c, _ in all_results} == {"1", "2"}

    @pytest.mark.asyncio
    async def test_multiple_handlers_per_agent(self):
        bus = MessageBus()
        results = []

        async def h1(msg):
            results.append("a")

        async def h2(msg):
            results.append("b")

        receiver_id = uuid4()
        bus.subscribe(str(receiver_id), h1)
        bus.subscribe(str(receiver_id), h2)

        msg = AgentMessage.create(
            type=MessageType.QUERY,
            sender_id=uuid4(),
            content="x",
            receiver_id=receiver_id,
        )
        await bus.publish(msg)
        assert results == ["a", "b"]
