"""Temporal workflow and activity definitions for ASTRA OS."""

from datetime import timedelta
from uuid import UUID

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from app.domain.entities.workflows.execution import ExecutionStatus
    from app.domain.entities.workflows.workflow import WorkflowStatus
    from app.infrastructure.temporal.shared import (
        CompileWorkflowInput,
        ExecuteStepInput,
        StepResult,
    )


@activity.defn
async def compile_workflow_activity(input: CompileWorkflowInput) -> list[dict]:
    from app.domain.entities.workflows.workflow import Workflow, WorkflowEdge, WorkflowNode
    from app.domain.services.workflow_compiler import compile_workflow
    wf = Workflow(
        id=UUID(input.workflow_id),
        organization_id=UUID(input.organization_id),
        name=input.name,
        status=WorkflowStatus.ACTIVE,
        nodes=[WorkflowNode(**n) for n in input.nodes],
        edges=[WorkflowEdge(**e) for e in input.edges],
    )
    compiled = compile_workflow(wf)
    return [s.__dict__ for s in compiled]


@activity.defn
async def execute_step_activity(input: ExecuteStepInput) -> StepResult:
    from app.domain.services.workflow_runner import ACTION_HANDLERS

    action_type = input.config.get("action_type", "")
    if action_type and action_type in ACTION_HANDLERS:
        handler = ACTION_HANDLERS[action_type]
        result = await handler(input.config, input.context)
        return StepResult(success=True, result=result)
    return StepResult(
        success=True,
        result={"step": input.label, "type": input.node_type, "status": "simulated"},
    )


@workflow.defn
class WorkflowExecutionWorkflow:
    @workflow.run
    async def run(self, input: CompileWorkflowInput) -> dict:
        steps = await workflow.execute_activity(
            compile_workflow_activity,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )

        context: dict = {}
        for i, step in enumerate(steps):
            step_result = await workflow.execute_activity(
                execute_step_activity,
                ExecuteStepInput(
                    step_id=step.get("id", f"step-{i}"),
                    label=step.get("label", f"Step {i}"),
                    node_type=step.get("node_type", "action"),
                    config=step.get("config", {}),
                    context=context,
                ),
                start_to_close_timeout=timedelta(seconds=120),
            )
            if not step_result.success:
                return {
                    "status": ExecutionStatus.FAILED.value,
                    "error": step_result.error,
                    "steps": steps,
                }
            if step_result.result:
                context.update(step_result.result)

        return {
            "status": ExecutionStatus.COMPLETED.value,
            "steps": steps,
        }
