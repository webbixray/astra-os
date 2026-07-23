import asyncio

from app.domain.common import now
from app.domain.entities.workflows.execution import (
    ExecutionStatus,
    StepStatus,
    WorkflowExecution,
)
from app.domain.entities.workflows.workflow import NodeType, Workflow
from app.domain.services.workflow_compiler import compile_workflow

ACTION_HANDLERS: dict[str, callable] = {}


def register_action_handler(action_type: str, handler: callable) -> None:
    ACTION_HANDLERS[action_type] = handler


class WorkflowRunner:
    def __init__(self, on_notification=None):
        self.on_notification = on_notification

    async def execute(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        context: dict | None = None,
    ) -> WorkflowExecution:
        try:
            compiled_steps = compile_workflow(workflow)
        except Exception as e:
            execution.fail(str(e))
            if self.on_notification:
                await self.on_notification(
                    type="workflow_failed",
                    title=f"Workflow failed: {workflow.name}",
                    body=f"Workflow compilation failed: {e}",
                    resource_type="workflow",
                    resource_id=str(workflow.id),
                )
            return execution

        execution.start()
        execution.steps = [s.to_execution_step() for s in compiled_steps]

        for i, compiled_step in enumerate(compiled_steps):
            step = execution.steps[i]
            step.status = StepStatus.RUNNING
            step.started_at = now()

            try:
                result = await self._execute_step(compiled_step, context or {})
                step.status = StepStatus.COMPLETED
                step.result = result
                step.completed_at = now()
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                step.completed_at = now()
                execution.fail(f"Step '{compiled_step.label}' failed: {e}")
                if self.on_notification:
                    await self.on_notification(
                        type="workflow_failed",
                        title=f"Workflow failed: {workflow.name}",
                        body=f"Step '{compiled_step.label}' failed: {e}",
                        resource_type="workflow",
                        resource_id=str(workflow.id),
                    )
                return execution

            if compiled_step.node_type == NodeType.DELAY:
                delay_seconds = compiled_step.config.get("seconds", 60)
                await asyncio.sleep(delay_seconds)

            if compiled_step.node_type == NodeType.APPROVAL:
                step.status = StepStatus.WAITING_APPROVAL
                execution.status = ExecutionStatus.PAUSED
                execution.updated_at = now()
                if self.on_notification:
                    await self.on_notification(
                        type="approval_request",
                        title=f"Approval required: {compiled_step.label}",
                        body=f"Workflow '{workflow.name}' needs approval at step '{compiled_step.label}'",
                        resource_type="workflow_execution",
                        resource_id=str(execution.id),
                    )
                return execution

        execution.complete()
        if self.on_notification:
            await self.on_notification(
                type="workflow_completed",
                title=f"Workflow completed: {workflow.name}",
                body=f"Workflow '{workflow.name}' completed successfully in {len(execution.steps)} steps",
                resource_type="workflow",
                resource_id=str(workflow.id),
            )
        return execution

    async def _execute_step(
        self,
        compiled_step,
        context: dict,
    ) -> dict:
        action_type = compiled_step.config.get("action_type", "")
        if action_type and action_type in ACTION_HANDLERS:
            handler = ACTION_HANDLERS[action_type]
            return await handler(compiled_step.config, context)

        return {
            "step": compiled_step.label,
            "type": compiled_step.node_type.value,
            "status": "simulated",
            "note": "Action handler not registered, returning simulated result",
        }
