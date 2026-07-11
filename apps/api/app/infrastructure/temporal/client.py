"""Temporal client wrapper for ASTRA OS."""

from uuid import UUID

from app.config import config


class TemporalWorkflowClient:
    def __init__(self):
        self._client = None
        self._imported = False
        self.enabled = bool(
            config.temporal_host and not config.temporal_host.startswith("localhost:")
        )

    async def get_client(self):
        if not self.enabled:
            return None
        if self._client is None and not self._imported:
            self._imported = True
            try:
                from temporalio.client import Client as TemporalClient

                self._client = await TemporalClient.connect(config.temporal_host)
            except ImportError:
                self.enabled = False
                return None
        return self._client

    async def execute_workflow(
        self,
        workflow_id: UUID,
        organization_id: UUID,
        name: str,
        nodes: list[dict],
        edges: list[dict],
    ) -> dict | None:
        client = await self.get_client()
        if client is None:
            return None

        from app.infrastructure.temporal.shared import CompileWorkflowInput
        from app.infrastructure.temporal.worker import TASK_QUEUE

        handle = await client.start_workflow(
            "WorkflowExecutionWorkflow",
            CompileWorkflowInput(
                workflow_id=str(workflow_id),
                organization_id=str(organization_id),
                name=name,
                nodes=nodes,
                edges=edges,
            ),
            id=f"workflow-{workflow_id}",
            task_queue=TASK_QUEUE,
        )
        return await handle.result()
