"""Temporal worker for ASTRA OS."""

import asyncio
import logging

from app.config import config

logger = logging.getLogger(__name__)

TASK_QUEUE = "astra-workflow-queue"


async def start_worker() -> None:
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker

        from app.infrastructure.temporal.workflows import (
            WorkflowExecutionWorkflow,
            compile_workflow_activity,
            execute_step_activity,
        )
    except ImportError:
        logger.exception("temporalio not installed — worker cannot start")
        return

    client = await Client.connect(config.temporal_host)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[WorkflowExecutionWorkflow],
        activities=[compile_workflow_activity, execute_step_activity],
    )
    logger.info("Temporal worker connected to %s, starting...", config.temporal_host)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(start_worker())
