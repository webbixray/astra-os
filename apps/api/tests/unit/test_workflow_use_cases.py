from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.workflows.workflow_use_cases import (
    CreateWorkflowUseCase,
    ExecuteWorkflowUseCase,
    GetWorkflowUseCase,
    ListWorkflowsUseCase,
    UpdateWorkflowUseCase,
)
from app.domain.entities.workflows.workflow import Workflow, WorkflowStatus
from app.domain.exceptions.domain_exceptions import EntityNotFoundError


def make_workflow(**overrides):
    return Workflow.create(
        organization_id=overrides.get("organization_id", uuid4()),
        name=overrides.get("name", "Test Workflow"),
        created_by=overrides.get("created_by", uuid4()),
        description=overrides.get("description", "A test workflow"),
    )


class TestCreateWorkflowUseCase:
    async def test_create(self):
        repo = MagicMock()
        repo.save = AsyncMock(return_value=make_workflow())

        use_case = CreateWorkflowUseCase(repo)
        result = await use_case.execute(uuid4(), "New Workflow", uuid4())

        assert result.name == "Test Workflow"


class TestGetWorkflowUseCase:
    async def test_found(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=make_workflow())

        use_case = GetWorkflowUseCase(repo)
        result = await use_case.execute(uuid4())

        assert result is not None
        assert result.name == "Test Workflow"

    async def test_not_found(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=None)

        use_case = GetWorkflowUseCase(repo)
        result = await use_case.execute(uuid4())

        assert result is None


class TestListWorkflowsUseCase:
    async def test_list(self):
        repo = MagicMock()
        repo.find_by_organization = AsyncMock(return_value=[make_workflow(), make_workflow()])

        use_case = ListWorkflowsUseCase(repo)
        result = await use_case.execute(uuid4())

        assert len(result) == 2

    async def test_list_filtered(self):
        repo = MagicMock()
        repo.find_by_organization = AsyncMock(return_value=[make_workflow()])

        use_case = ListWorkflowsUseCase(repo)
        result = await use_case.execute(uuid4(), status="active")

        assert len(result) == 1

    async def test_list_empty(self):
        repo = MagicMock()
        repo.find_by_organization = AsyncMock(return_value=[])

        use_case = ListWorkflowsUseCase(repo)
        result = await use_case.execute(uuid4())

        assert result == []


class TestUpdateWorkflowUseCase:
    async def test_update_all_fields(self):
        repo = MagicMock()
        workflow = make_workflow()
        repo.find_by_id = AsyncMock(return_value=workflow)
        repo.save = AsyncMock(return_value=workflow)

        use_case = UpdateWorkflowUseCase(repo)
        result = await use_case.execute(
            uuid4(), name="Updated", description="New desc", status="active"
        )

        assert result.name == "Updated"

    async def test_update_not_found(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=None)

        use_case = UpdateWorkflowUseCase(repo)
        result = await use_case.execute(uuid4(), name="Updated")

        assert result is None

    async def test_update_partial(self):
        repo = MagicMock()
        workflow = make_workflow()
        repo.find_by_id = AsyncMock(return_value=workflow)
        repo.save = AsyncMock(return_value=workflow)

        use_case = UpdateWorkflowUseCase(repo)
        result = await use_case.execute(uuid4(), nodes=[{"id": "1"}], edges=[{"id": "e1"}])

        assert result is not None


class TestExecuteWorkflowUseCase:
    async def test_workflow_not_found(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=None)

        use_case = ExecuteWorkflowUseCase(repo)
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(uuid4(), uuid4(), uuid4())

    async def test_execute_with_temporal(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=make_workflow())
        exec_model = MagicMock()
        exec_model.id = uuid4()
        exec_model.status = "completed"
        exec_model.steps = []
        repo.save_execution = AsyncMock(return_value=exec_model)

        use_case = ExecuteWorkflowUseCase(repo)
        use_case.temporal = MagicMock()
        use_case.temporal.execute_workflow = AsyncMock(
            return_value={"status": "completed", "steps": []}
        )

        result = await use_case.execute(uuid4(), uuid4(), uuid4())

        assert result["engine"] == "temporal"

    async def test_execute_with_sync_runner(self):
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=make_workflow())
        exec_model = MagicMock()
        exec_model.id = uuid4()
        exec_model.status = "running"
        exec_model.steps = []
        exec_model.error = None

        runner_execution = MagicMock()
        runner_execution.id = uuid4()
        runner_execution.status = WorkflowStatus.COMPLETED
        runner_execution.steps = []
        runner_execution.error = None

        repo.save_execution = AsyncMock(side_effect=[exec_model, runner_execution])

        use_case = ExecuteWorkflowUseCase(repo)
        use_case.temporal = MagicMock()
        use_case.temporal.execute_workflow = AsyncMock(return_value=None)

        runner = MagicMock()
        runner.execute = AsyncMock(return_value=runner_execution)
        use_case.runner = runner

        result = await use_case.execute(uuid4(), uuid4(), uuid4())

        assert result["engine"] == "sync"
