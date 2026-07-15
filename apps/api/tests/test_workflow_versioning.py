"""Tests for Workflow Versioning — M5 Workflow Engine."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.domain.entities.workflows.version import WorkflowVersion
from app.domain.entities.workflows.workflow import (
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from app.domain.services.workflow_versioning import (
    WorkflowReplayService,
    WorkflowVersionService,
)


class TestWorkflowVersion:
    def test_version_creation_from_workflow(self):
        workflow = Workflow.create(
            organization_id=uuid4(),
            name="Test Workflow",
            created_by=uuid4(),
            description="A test workflow",
        )
        # Add some nodes
        workflow.add_node(WorkflowNode.create("a1", NodeType.ACTION, "Action 1"))
        workflow.add_edge(WorkflowEdge.create("e1", "trigger-1", "a1"))

        version = WorkflowVersion.from_workflow(
            workflow=workflow,
            version_number=1,
            created_by=uuid4(),
            change_summary="Initial version",
        )

        assert version.workflow_id == workflow.id
        assert version.version_number == 1
        assert version.name == "Test Workflow"
        assert version.description == "A test workflow"
        assert len(version.nodes) == 3  # trigger + action + end
        assert len(version.edges) == 2
        assert version.change_summary == "Initial version"

    def test_version_to_dict(self):
        version = WorkflowVersion(
            id=uuid4(),
            workflow_id=uuid4(),
            organization_id=uuid4(),
            version_number=1,
            name="Test",
            description="Desc",
            change_summary="Summary",
            created_by=uuid4(),
            created_at=datetime.now(),
        )
        d = version.to_dict()
        assert d["version_number"] == 1
        assert d["name"] == "Test"
        assert d["change_summary"] == "Summary"

    def test_version_to_workflow_restoration(self):
        workflow = Workflow.create(
            organization_id=uuid4(),
            name="Original",
            created_by=uuid4(),
        )

        version = WorkflowVersion.from_workflow(
            workflow=workflow,
            version_number=1,
            created_by=uuid4(),
        )

        restored = version.to_workflow(created_by=uuid4())
        assert restored.name == "Original"
        assert restored.status == WorkflowStatus.DRAFT
        assert len(restored.nodes) == 2  # trigger + end


class MockVersionRepo:
    """Mock repository for version tests."""

    def __init__(self):
        self.versions: dict[str, WorkflowVersion] = {}
        self.workflows: dict[str, Workflow] = {}

    async def find_by_id(self, workflow_id: str) -> Workflow | None:
        return self.workflows.get(str(workflow_id))

    async def save(self, workflow: Workflow) -> Workflow:
        self.workflows[str(workflow.id)] = workflow
        return workflow

    async def save_version(self, version: WorkflowVersion) -> WorkflowVersion:
        self.versions[str(version.id)] = version
        return version

    async def find_versions_by_workflow(self, workflow_id: UUID) -> list[WorkflowVersion]:
        return [v for v in self.versions.values() if v.workflow_id == workflow_id]

    async def find_version(self, workflow_id: UUID, version_number: int) -> WorkflowVersion | None:
        for v in self.versions.values():
            if v.workflow_id == workflow_id and v.version_number == version_number:
                return v
        return None


class TestWorkflowVersionService:
    @pytest.fixture
    def repo(self):
        return MockVersionRepo()

    @pytest.fixture
    def service(self, repo):
        return WorkflowVersionService(repo)

    @pytest.fixture
    def sample_workflow(self):
        return Workflow.create(
            organization_id=uuid4(),
            name="Test Workflow",
            created_by=uuid4(),
        )

    @pytest.mark.asyncio
    async def test_create_version(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)

        version = await service.create_version(
            workflow=sample_workflow,
            created_by=uuid4(),
            change_summary="First version",
        )

        assert version.workflow_id == sample_workflow.id
        assert version.version_number == 1
        assert version.change_summary == "First version"
        assert len(repo.versions) == 1

    @pytest.mark.asyncio
    async def test_create_multiple_versions(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)
        user_id = uuid4()

        v1 = await service.create_version(sample_workflow, user_id, "v1")
        v2 = await service.create_version(sample_workflow, user_id, "v2")
        v3 = await service.create_version(sample_workflow, user_id, "v3")

        assert v1.version_number == 1
        assert v2.version_number == 2
        assert v3.version_number == 3

    @pytest.mark.asyncio
    async def test_list_versions(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)
        user_id = uuid4()

        await service.create_version(sample_workflow, user_id, "v1")
        await service.create_version(sample_workflow, user_id, "v2")
        await service.create_version(sample_workflow, user_id, "v3")

        versions = await service.list_versions(sample_workflow.id)
        assert len(versions) == 3
        # Should be sorted newest first
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    @pytest.mark.asyncio
    async def test_get_version(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)
        user_id = uuid4()

        await service.create_version(sample_workflow, user_id, "v1")
        await service.create_version(sample_workflow, user_id, "v2")

        v1 = await service.get_version(sample_workflow.id, 1)
        assert v1 is not None
        assert v1.version_number == 1

        v3 = await service.get_version(sample_workflow.id, 3)
        assert v3 is None

    @pytest.mark.asyncio
    async def test_restore_version(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)
        user_id = uuid4()

        v1 = await service.create_version(sample_workflow, user_id, "v1")
        # Modify workflow
        sample_workflow.add_node(WorkflowNode.create("a1", NodeType.ACTION, "New Action"))
        await repo.save(sample_workflow)
        v2 = await service.create_version(sample_workflow, user_id, "v2")

        # Restore v1
        restored = await service.restore_version(
            workflow_id=sample_workflow.id,
            version_number=1,
            restored_by=user_id,
        )

        assert restored.name == "Test Workflow"
        assert len(restored.nodes) == 2  # Original trigger + end only

    @pytest.mark.asyncio
    async def test_compare_versions(self, service, repo, sample_workflow):
        await repo.save(sample_workflow)
        user_id = uuid4()

        v1 = await service.create_version(sample_workflow, user_id, "v1")
        sample_workflow.add_node(WorkflowNode.create("a1", NodeType.ACTION, "Action 1"))
        await repo.save(sample_workflow)
        v2 = await service.create_version(sample_workflow, user_id, "v2")

        comparison = await service.compare_versions(sample_workflow.id, 1, 2)

        assert "version_a" in comparison
        assert "version_b" in comparison
        assert "nodes_added" in comparison
        assert "nodes_removed" in comparison
        assert "nodes_modified" in comparison
        assert len(comparison["nodes_added"]) == 1
        assert comparison["nodes_added"][0]["label"] == "Action 1"


class TestWorkflowReplayService:
    @pytest.fixture
    def execution_repo(self):
        class MockExecutionRepo:
            def __init__(self):
                self.executions = {}

            async def find_by_id(self, execution_id: UUID):
                return self.executions.get(str(execution_id))

            async def find_workflow_by_id(self, workflow_id: UUID):
                return None

            async def save_execution(self, execution):
                self.executions[str(execution.id)] = execution
                return execution
        return MockExecutionRepo()

    @pytest.fixture
    def version_service(self):
        return MockVersionService()

    @pytest.fixture
    def replay_service(self, execution_repo, version_service):
        return WorkflowReplayService(execution_repo, version_service)

    @pytest.mark.asyncio
    async def test_get_replay_not_found(self, replay_service):
        result = await replay_service.get_replay(uuid4())
        assert result is None


class MockVersionService:
    async def get_version(self, workflow_id: UUID, version_number: int):
        return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
