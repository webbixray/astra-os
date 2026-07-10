from uuid import uuid4

import pytest

from app.domain.entities.workflows.execution import (
    ExecutionStatus,
    ExecutionStep,
    StepStatus,
    WorkflowExecution,
)
from app.domain.entities.workflows.workflow import (
    NODE_CATEGORIES,
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from app.domain.exceptions.domain_exceptions import ValidationError


class TestWorkflowNode:
    def test_create_node(self):
        node = WorkflowNode.create(
            id="n1", type=NodeType.ACTION, label="Do Thing", config={"x": 1}
        )
        assert node.id == "n1"
        assert node.type == NodeType.ACTION
        assert node.label == "Do Thing"
        assert node.config == {"x": 1}

    def test_create_node_default_label(self):
        node = WorkflowNode.create(id="n1", type=NodeType.TRIGGER, label="")
        assert node.label == "trigger"

    def test_create_node_default_config(self):
        node = WorkflowNode.create(id="n1", type=NodeType.ACTION, label="X")
        assert node.config == {}


class TestWorkflowEdge:
    def test_create_edge(self):
        edge = WorkflowEdge.create(id="e1", source_id="a", target_id="b", label="link")
        assert edge.id == "e1"
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.label == "link"


class TestWorkflow:
    def test_create_workflow_defaults(self):
        org_id = uuid4()
        user_id = uuid4()
        wf = Workflow.create(organization_id=org_id, name="My WF", created_by=user_id)
        assert wf.organization_id == org_id
        assert wf.name == "My WF"
        assert wf.created_by == user_id
        assert wf.status == WorkflowStatus.DRAFT
        assert len(wf.nodes) == 2
        assert len(wf.edges) == 1
        node_ids = {n.id for n in wf.nodes}
        assert "trigger-1" in node_ids
        assert "end-1" in node_ids
        assert wf.edges[0].source_id == "trigger-1"
        assert wf.edges[0].target_id == "end-1"

    def test_add_node(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        node = WorkflowNode.create(id="n2", type=NodeType.ACTION, label="Step 2")
        wf.add_node(node)
        assert len(wf.nodes) == 3
        assert node in wf.nodes

    def test_remove_node_removes_incident_edges(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        wf.add_node(WorkflowNode.create(id="mid", type=NodeType.ACTION, label="Mid"))
        wf.add_edge(WorkflowEdge.create(id="e1", source_id="trigger-1", target_id="mid"))
        wf.add_edge(WorkflowEdge.create(id="e2", source_id="mid", target_id="end-1"))
        assert len(wf.edges) == 3
        wf.remove_node("mid")
        assert len(wf.nodes) == 2
        assert len(wf.edges) == 1
        assert wf.edges[0].id == "e-trigger-end"

    def test_add_edge(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        edge = WorkflowEdge.create(id="e-new", source_id="trigger-1", target_id="end-1")
        wf.add_edge(edge)
        assert edge in wf.edges

    def test_remove_edge(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        wf.remove_edge("e-trigger-end")
        assert len(wf.edges) == 0

    def test_transition_allowed(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        wf.transition_to(WorkflowStatus.ACTIVE)
        assert wf.status == WorkflowStatus.ACTIVE
        wf.transition_to(WorkflowStatus.COMPLETED)
        assert wf.status == WorkflowStatus.COMPLETED

    def test_transition_disallowed_raises(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        with pytest.raises(ValidationError):
            wf.transition_to(WorkflowStatus.COMPLETED)  # DRAFT -> COMPLETED not allowed
        assert wf.status == WorkflowStatus.DRAFT
        wf.transition_to(WorkflowStatus.ACTIVE)
        with pytest.raises(ValidationError):
            wf.transition_to(WorkflowStatus.DRAFT)  # ACTIVE -> DRAFT not allowed
        assert wf.status == WorkflowStatus.ACTIVE

    def test_transition_from_archived_raises(self):
        wf = Workflow.create(organization_id=uuid4(), name="X", created_by=uuid4())
        wf.transition_to(WorkflowStatus.ARCHIVED)
        assert wf.status == WorkflowStatus.ARCHIVED
        with pytest.raises(ValidationError):
            wf.transition_to(WorkflowStatus.DRAFT)
        assert wf.status == WorkflowStatus.ARCHIVED


class TestWorkflowExecution:
    def test_create_execution(self):
        ex = WorkflowExecution.create(workflow_id=uuid4(), organization_id=uuid4(), triggered_by=uuid4())
        assert ex.workflow_id is not None
        assert ex.organization_id is not None
        assert ex.triggered_by is not None
        assert ex.status == ExecutionStatus.PENDING
        assert ex.steps == []

    def test_start_transition(self):
        ex = WorkflowExecution.create(workflow_id=uuid4(), organization_id=uuid4(), triggered_by=uuid4())
        ex.start()
        assert ex.status == ExecutionStatus.RUNNING

    def test_complete_transition(self):
        ex = WorkflowExecution.create(workflow_id=uuid4(), organization_id=uuid4(), triggered_by=uuid4())
        ex.complete()
        assert ex.status == ExecutionStatus.COMPLETED

    def test_fail_transition(self):
        ex = WorkflowExecution.create(workflow_id=uuid4(), organization_id=uuid4(), triggered_by=uuid4())
        ex.fail("boom")
        assert ex.status == ExecutionStatus.FAILED
        assert ex.error == "boom"


class TestExecutionStep:
    def test_defaults(self):
        step = ExecutionStep(id="s1", node_id="n1")
        assert step.status == StepStatus.PENDING
        assert step.result is None
        assert step.error is None
        assert step.started_at is None
        assert step.completed_at is None


class TestNODE_CATEGORIES:
    def test_covers_all_node_types(self):
        for nt in NodeType:
            assert nt in NODE_CATEGORIES
            assert isinstance(NODE_CATEGORIES[nt], str)
            assert len(NODE_CATEGORIES[nt]) > 0
