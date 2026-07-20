from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.entities.workflows.execution import (
    ExecutionStatus,
    StepStatus,
    WorkflowExecution,
)
from app.domain.entities.workflows.workflow import (
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
)
from app.domain.services.workflow_compiler import (
    CompiledStep,
    CompileError,
    compile_workflow,
)
from app.domain.services.workflow_runner import (
    ACTION_HANDLERS,
    WorkflowRunner,
    register_action_handler,
)


class TestCompiledStep:
    def test_to_execution_step(self):
        cs = CompiledStep(
            order=0,
            node_id="n1",
            node_type=NodeType.ACTION,
            label="Step 1",
            config={"action_type": "test"},
        )
        es = cs.to_execution_step()
        assert es.id == "step-0-n1"
        assert es.node_id == "n1"
        assert es.status == StepStatus.PENDING


class TestCompileWorkflow:
    def test_empty_nodes_raises(self):
        wf = Workflow(organization_id=uuid4(), name="Empty", created_by=uuid4())
        wf.nodes = []
        with pytest.raises(CompileError, match="Workflow has no nodes"):
            compile_workflow(wf)

    def test_no_trigger_raises(self):
        wf = Workflow(organization_id=uuid4(), name="No Trigger", created_by=uuid4())
        wf.nodes = [WorkflowNode.create(id="n1", type=NodeType.ACTION, label="Action")]
        with pytest.raises(CompileError, match="must have a trigger node"):
            compile_workflow(wf)

    def test_single_trigger_to_end(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Simple", created_by=user)
        # Default has trigger-1 -> end-1
        steps = compile_workflow(wf)
        assert len(steps) == 1
        assert steps[0].node_id == "trigger-1"
        assert steps[0].node_type == NodeType.TRIGGER

    def test_linear_chain(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow(organization_id=org, name="Chain", created_by=user)
        wf.nodes = [
            WorkflowNode.create(id="t1", type=NodeType.TRIGGER, label="Start"),
            WorkflowNode.create(id="a1", type=NodeType.ACTION, label="Action 1"),
            WorkflowNode.create(id="a2", type=NodeType.ACTION, label="Action 2"),
            WorkflowNode.create(id="e1", type=NodeType.END, label="End"),
        ]
        wf.edges = [
            WorkflowEdge.create(id="e1", source_id="t1", target_id="a1"),
            WorkflowEdge.create(id="e2", source_id="a1", target_id="a2"),
            WorkflowEdge.create(id="e3", source_id="a2", target_id="e1"),
        ]
        steps = compile_workflow(wf)
        assert len(steps) == 3  # trigger, action1, action2 (END excluded)
        assert steps[0].node_id == "t1"
        assert steps[1].node_id == "a1"
        assert steps[2].node_id == "a2"

    def test_skips_end_node(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow(organization_id=org, name="X", created_by=user)
        wf.nodes = [
            WorkflowNode.create(id="t1", type=NodeType.TRIGGER, label="Start"),
            WorkflowNode.create(id="e1", type=NodeType.END, label="End"),
        ]
        wf.edges = [WorkflowEdge.create(id="e1", source_id="t1", target_id="e1")]
        steps = compile_workflow(wf)
        assert len(steps) == 1
        assert steps[0].node_id == "t1"

    def test_visits_each_node_once(self):
        """Diamond DAG: t1 -> a1, t1 -> a2, a1 -> e1, a2 -> e1"""
        org = uuid4()
        user = uuid4()
        wf = Workflow(organization_id=org, name="Diamond", created_by=user)
        wf.nodes = [
            WorkflowNode.create(id="t1", type=NodeType.TRIGGER, label="Start"),
            WorkflowNode.create(id="a1", type=NodeType.ACTION, label="Action 1"),
            WorkflowNode.create(id="a2", type=NodeType.ACTION, label="Action 2"),
            WorkflowNode.create(id="e1", type=NodeType.END, label="End"),
        ]
        wf.edges = [
            WorkflowEdge.create(id="e1", source_id="t1", target_id="a1"),
            WorkflowEdge.create(id="e2", source_id="t1", target_id="a2"),
            WorkflowEdge.create(id="e3", source_id="a1", target_id="e1"),
            WorkflowEdge.create(id="e4", source_id="a2", target_id="e1"),
        ]
        steps = compile_workflow(wf)
        # Should visit t1, then a1, then a2 (or a2 then a1) - each exactly once
        assert len(steps) == 3
        node_ids = {s.node_id for s in steps}
        assert node_ids == {"t1", "a1", "a2"}

    def test_multiple_triggers_uses_first(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow(organization_id=org, name="Multi", created_by=user)
        wf.nodes = [
            WorkflowNode.create(id="t1", type=NodeType.TRIGGER, label="Trigger 1"),
            WorkflowNode.create(id="t2", type=NodeType.TRIGGER, label="Trigger 2"),
            WorkflowNode.create(id="a1", type=NodeType.ACTION, label="Action"),
        ]
        wf.edges = [
            WorkflowEdge.create(id="e1", source_id="t1", target_id="a1"),
        ]
        steps = compile_workflow(wf)
        assert len(steps) == 2
        assert steps[0].node_id == "t1"


class TestRegisterActionHandler:
    def teardown_method(self):
        ACTION_HANDLERS.clear()

    def test_register_and_lookup(self):
        async def handler(config, ctx):
            return {"ok": True}

        register_action_handler("test_action", handler)
        assert ACTION_HANDLERS["test_action"] == handler


class TestWorkflowRunner:
    @pytest.mark.asyncio
    async def test_compile_failure_sets_failed_and_notifies(self):
        runner = WorkflowRunner(on_notification=AsyncMock())
        wf = Workflow(organization_id=uuid4(), name="Bad", created_by=uuid4())
        wf.nodes = []
        ex = WorkflowExecution.create(
            workflow_id=uuid4(), organization_id=uuid4(), triggered_by=uuid4()
        )
        result = await runner.execute(wf, ex)
        assert result.status == ExecutionStatus.FAILED
        assert "no nodes" in result.error.lower()
        runner.on_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        runner = WorkflowRunner()
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Good", created_by=user)
        ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
        result = await runner.execute(wf, ex)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.steps) == 1  # only trigger step
        assert result.steps[0].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_step_failure_stops_execution(self):
        async def failing_handler(config, ctx):
            raise ValueError("boom")

        register_action_handler("fail_action", failing_handler)
        try:
            runner = WorkflowRunner()
            org = uuid4()
            user = uuid4()
            wf = Workflow.create(organization_id=org, name="Fail", created_by=user)
            # Add action node after trigger
            wf.nodes.append(
                WorkflowNode.create(
                    id="a1",
                    type=NodeType.ACTION,
                    label="Failing",
                    config={"action_type": "fail_action"},
                )
            )
            wf.edges.append(WorkflowEdge.create(id="e2", source_id="trigger-1", target_id="a1"))
            ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
            result = await runner.execute(wf, ex)
            assert result.status == ExecutionStatus.FAILED
            assert "boom" in result.error
            # Second step should have failed status
            failed_steps = [s for s in result.steps if s.status == StepStatus.FAILED]
            assert len(failed_steps) == 1
        finally:
            ACTION_HANDLERS.clear()

    @pytest.mark.asyncio
    async def test_delay_node_sleeps(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Delay", created_by=user)
        wf.nodes.append(
            WorkflowNode.create(
                id="d1",
                type=NodeType.DELAY,
                label="Wait",
                config={"seconds": 0},  # use 0 for test
            )
        )
        wf.edges.append(WorkflowEdge.create(id="e2", source_id="trigger-1", target_id="d1"))
        ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
        runner = WorkflowRunner()
        # Should complete without hanging
        result = await runner.execute(wf, ex)
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_approval_node_pauses(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Approval", created_by=user)
        wf.nodes.append(WorkflowNode.create(id="ap1", type=NodeType.APPROVAL, label="Approve me"))
        wf.edges.append(WorkflowEdge.create(id="e2", source_id="trigger-1", target_id="ap1"))
        ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
        runner = WorkflowRunner(on_notification=AsyncMock())
        result = await runner.execute(wf, ex)
        assert result.status == ExecutionStatus.PAUSED
        approval_steps = [s for s in result.steps if s.status == StepStatus.WAITING_APPROVAL]
        assert len(approval_steps) == 1
        runner.on_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_without_handler_returns_simulated(self):
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Sim", created_by=user)
        wf.nodes.append(
            WorkflowNode.create(
                id="a1", type=NodeType.ACTION, label="Do Thing", config={"action_type": "unknown"}
            )
        )
        wf.edges.append(WorkflowEdge.create(id="e2", source_id="trigger-1", target_id="a1"))
        ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
        runner = WorkflowRunner()
        result = await runner.execute(wf, ex)
        assert result.status == ExecutionStatus.COMPLETED
        action_step = next(s for s in result.steps if s.node_id == "a1")
        assert action_step.status == StepStatus.COMPLETED
        assert action_step.result["status"] == "simulated"

    @pytest.mark.asyncio
    async def test_action_with_registered_handler(self):
        async def my_handler(config, ctx):
            return {"custom": "result", "from": config.get("value")}

        register_action_handler("my_custom", my_handler)
        try:
            org = uuid4()
            user = uuid4()
            wf = Workflow.create(organization_id=org, name="Handler", created_by=user)
            wf.nodes.append(
                WorkflowNode.create(
                    id="a1",
                    type=NodeType.ACTION,
                    label="Custom",
                    config={"action_type": "my_custom", "value": "test123"},
                )
            )
            wf.edges.append(WorkflowEdge.create(id="e2", source_id="trigger-1", target_id="a1"))
            ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
            runner = WorkflowRunner()
            result = await runner.execute(wf, ex)
            assert result.status == ExecutionStatus.COMPLETED
            action_step = next(s for s in result.steps if s.node_id == "a1")
            assert action_step.result == {"custom": "result", "from": "test123"}
        finally:
            ACTION_HANDLERS.clear()

    @pytest.mark.asyncio
    async def test_complete_sends_notification(self):
        notifier = AsyncMock()
        runner = WorkflowRunner(on_notification=notifier)
        org = uuid4()
        user = uuid4()
        wf = Workflow.create(organization_id=org, name="Notify", created_by=user)
        ex = WorkflowExecution.create(workflow_id=wf.id, organization_id=org, triggered_by=user)
        await runner.execute(wf, ex)
        notifier.assert_called_once()
        call = notifier.call_args[1]
        assert call["type"] == "workflow_completed"
        assert "completed successfully" in call["body"]


class TestWorkflowRunnerExecuteStep:
    @pytest.mark.asyncio
    async def test_execute_step_with_handler(self):
        async def handler(config, ctx):
            return {"from_handler": True}

        register_action_handler("test", handler)
        try:
            runner = WorkflowRunner()
            step = CompiledStep(
                order=0,
                node_id="n1",
                node_type=NodeType.ACTION,
                label="Test",
                config={"action_type": "test"},
            )
            result = await runner._execute_step(step, {})
            assert result["from_handler"] is True
        finally:
            ACTION_HANDLERS.clear()

    @pytest.mark.asyncio
    async def test_execute_step_without_handler(self):
        runner = WorkflowRunner()
        step = CompiledStep(
            order=0, node_id="n1", node_type=NodeType.ACTION, label="Test", config={}
        )
        result = await runner._execute_step(step, {})
        assert result["status"] == "simulated"
