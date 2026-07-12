"""Tests for Workflow Templates — M5 Workflow Engine."""

import pytest
from uuid import uuid4

from app.domain.entities.workflows.workflow import (
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)
from app.domain.services.workflow_templates import (
    WorkflowTemplate,
    WorkflowTemplateRegistry,
    template_registry,
)


# ---------------------------------------------------------------------------
# WorkflowTemplate unit tests
# ---------------------------------------------------------------------------

class TestWorkflowTemplate:
    def test_template_creation(self):
        nodes = [
            WorkflowNode.create("t1", NodeType.TRIGGER, "Start"),
            WorkflowNode.create("a1", NodeType.ACTION, "Do Thing"),
            WorkflowNode.create("e1", NodeType.END, "End"),
        ]
        edges = [
            WorkflowEdge.create("e1", "t1", "a1"),
            WorkflowEdge.create("e2", "a1", "e1"),
        ]
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            nodes=nodes,
            edges=edges,
            estimated_duration_minutes=30,
            tags=["test", "example"],
        )
        assert template.template_id == "test_template"
        assert template.name == "Test Template"
        assert len(template.nodes) == 3
        assert len(template.edges) == 2
        assert template.category == "test"
        assert template.estimated_duration_minutes == 30
        assert "test" in template.tags

    def test_template_to_dict(self):
        template = WorkflowTemplate(
            template_id="tmpl_1",
            name="My Template",
            description="Desc",
            category="campaign",
            nodes=[WorkflowNode.create("t1", NodeType.TRIGGER, "Start")],
            edges=[WorkflowEdge.create("e1", "t1", "end")],
            estimated_duration_minutes=60,
            tags=["campaign"],
        )
        d = template.to_dict()
        assert d["template_id"] == "tmpl_1"
        assert d["name"] == "My Template"
        assert d["node_count"] == 1
        assert d["edge_count"] == 1
        assert d["estimated_duration_minutes"] == 60
        assert d["tags"] == ["campaign"]

    def test_template_instantiate_creates_workflow(self):
        template = WorkflowTemplate(
            template_id="inst_1",
            name="Instantiate Test",
            description="Test instantiation",
            category="test",
            nodes=[
                WorkflowNode.create("t1", NodeType.TRIGGER, "Start"),
                WorkflowNode.create("e1", NodeType.END, "End"),
            ],
            edges=[WorkflowEdge.create("e1", "t1", "e1")],
        )
        org_id = uuid4()
        user_id = uuid4()
        workflow = template.instantiate(organization_id=org_id, created_by=user_id)

        assert isinstance(workflow, Workflow)
        assert workflow.organization_id == org_id
        assert workflow.created_by == user_id
        assert workflow.name == "Instantiate Test"
        assert len(workflow.nodes) == 2
        assert len(workflow.edges) == 1

    def test_template_instantiate_custom_name(self):
        template = WorkflowTemplate(
            template_id="name_test",
            name="Default Name",
            description="Desc",
            category="test",
            nodes=[],
            edges=[],
        )
        workflow = template.instantiate(
            organization_id=uuid4(),
            created_by=uuid4(),
            name="Custom Name",
        )
        assert workflow.name == "Custom Name"

    def test_template_instantiate_preserves_node_structure(self):
        nodes = [
            WorkflowNode.create("t1", NodeType.TRIGGER, "Trigger", {"trigger_type": "manual"}),
            WorkflowNode.create("a1", NodeType.ACTION, "Action 1", {"action_type": "content.generate"}),
            WorkflowNode.create("c1", NodeType.CONDITION, "Check", {"condition": "score > 80"}),
            WorkflowNode.create("e1", NodeType.END, "Done"),
        ]
        template = WorkflowTemplate(
            template_id="struct_test",
            name="Structure Test",
            description="",
            category="test",
            nodes=nodes,
            edges=[],
        )
        workflow = template.instantiate(organization_id=uuid4(), created_by=uuid4())
        assert len(workflow.nodes) == 4
        assert workflow.nodes[0].type == NodeType.TRIGGER
        assert workflow.nodes[0].config.get("trigger_type") == "manual"
        assert workflow.nodes[1].config.get("action_type") == "content.generate"
        assert workflow.nodes[2].type == NodeType.CONDITION


# ---------------------------------------------------------------------------
# WorkflowTemplateRegistry tests
# ---------------------------------------------------------------------------

class TestWorkflowTemplateRegistry:
    def test_registry_has_builtin_templates(self):
        registry = WorkflowTemplateRegistry()
        templates = registry.list_templates()
        assert len(templates) == 4

    def test_registry_get_template(self):
        registry = WorkflowTemplateRegistry()
        tmpl = registry.get_template("campaign_launch")
        assert tmpl is not None
        assert tmpl.name == "Campaign Launch"

    def test_registry_get_nonexistent_template(self):
        registry = WorkflowTemplateRegistry()
        tmpl = registry.get_template("nonexistent")
        assert tmpl is None

    def test_registry_list_by_category(self):
        registry = WorkflowTemplateRegistry()
        campaign = registry.list_templates(category="campaign")
        assert len(campaign) == 1
        assert campaign[0].template_id == "campaign_launch"

        content = registry.list_templates(category="content")
        assert len(content) == 1
        assert content[0].template_id == "creative_review"

    def test_registry_list_nonexistent_category(self):
        registry = WorkflowTemplateRegistry()
        result = registry.list_templates(category="nonexistent")
        assert len(result) == 0

    def test_registry_register_custom_template(self):
        registry = WorkflowTemplateRegistry()
        custom = WorkflowTemplate(
            template_id="custom_1",
            name="Custom Template",
            description="A custom template",
            category="custom",
            nodes=[WorkflowNode.create("t1", NodeType.TRIGGER, "Start")],
            edges=[],
        )
        registry.register_template(custom)
        assert registry.get_template("custom_1") is not None
        assert len(registry.list_templates()) == 5  # 4 builtin + 1 custom

    def test_registry_register_overwrites_existing(self):
        registry = WorkflowTemplateRegistry()
        original = registry.get_template("campaign_launch")
        assert original is not None

        new_version = WorkflowTemplate(
            template_id="campaign_launch",
            name="Campaign Launch V2",
            description="Updated",
            category="campaign",
            nodes=[],
            edges=[],
        )
        registry.register_template(new_version)
        updated = registry.get_template("campaign_launch")
        assert updated.name == "Campaign Launch V2"

    def test_registry_instantiate_template(self):
        registry = WorkflowTemplateRegistry()
        org_id = uuid4()
        user_id = uuid4()
        workflow = registry.instantiate_template("campaign_launch", org_id, user_id)
        assert workflow is not None
        assert isinstance(workflow, Workflow)
        assert workflow.organization_id == org_id
        assert workflow.name == "Campaign Launch"

    def test_registry_instantiate_nonexistent(self):
        registry = WorkflowTemplateRegistry()
        result = registry.instantiate_template("nonexistent", uuid4(), uuid4())
        assert result is None

    def test_registry_instantiate_custom_name(self):
        registry = WorkflowTemplateRegistry()
        workflow = registry.instantiate_template(
            "creative_review", uuid4(), uuid4(), name="My Review Flow"
        )
        assert workflow.name == "My Review Flow"

    def test_builtin_template_categories(self):
        registry = WorkflowTemplateRegistry()
        categories = {t.category for t in registry.list_templates()}
        assert "campaign" in categories
        assert "content" in categories
        assert "optimization" in categories
        assert "compliance" in categories

    def test_global_registry_singleton(self):
        """The module-level template_registry is a singleton."""
        assert template_registry is not None
        templates = template_registry.list_templates()
        assert len(templates) == 4


# ---------------------------------------------------------------------------
# Built-in template structure tests
# ---------------------------------------------------------------------------

class TestBuiltinTemplateStructure:
    def test_campaign_launch_has_trigger_and_end(self):
        tmpl = template_registry.get_template("campaign_launch")
        types = [n.type for n in tmpl.nodes]
        assert NodeType.TRIGGER in types
        assert NodeType.END in types

    def test_campaign_launch_has_approval(self):
        tmpl = template_registry.get_template("campaign_launch")
        types = [n.type for n in tmpl.nodes]
        assert NodeType.APPROVAL in types

    def test_creative_review_has_loop(self):
        tmpl = template_registry.get_template("creative_review")
        # Creative review has a revision loop: condition → revision → back to action
        assert len(tmpl.edges) == 7  # 7 edges for the loop structure
        # Check there's an edge that creates a cycle
        edge_targets = {(e.source_id, e.target_id) for e in tmpl.edges}
        # "a3" (Request Revision) goes back to "a1" (AI Content Review)
        assert ("a3", "a1") in edge_targets

    def test_optimization_loop_has_cron_trigger(self):
        tmpl = template_registry.get_template("optimization_loop")
        trigger = [n for n in tmpl.nodes if n.type == NodeType.TRIGGER][0]
        assert trigger.config.get("trigger_type") == "cron"
        assert trigger.config.get("cron") == "0 9 * * *"

    def test_brand_compliance_has_two_checks(self):
        tmpl = template_registry.get_template("brand_compliance")
        actions = [n for n in tmpl.nodes if n.type == NodeType.ACTION]
        action_types = [n.config.get("action_type") for n in actions]
        assert "brand.check" in action_types
        assert "brand.visual_check" in action_types

    def test_all_templates_have_valid_edges(self):
        """All edges reference existing nodes."""
        for tmpl in template_registry.list_templates():
            node_ids = {n.id for n in tmpl.nodes}
            for edge in tmpl.edges:
                assert edge.source_id in node_ids, (
                    f"Template '{tmpl.template_id}' edge '{edge.id}' "
                    f"references unknown source '{edge.source_id}'"
                )
                assert edge.target_id in node_ids, (
                    f"Template '{tmpl.template_id}' edge '{edge.id}' "
                    f"references unknown target '{edge.target_id}'"
                )

    def test_all_templates_have_estimated_duration(self):
        for tmpl in template_registry.list_templates():
            assert tmpl.estimated_duration_minutes > 0, (
                f"Template '{tmpl.template_id}' has no estimated duration"
            )

    def test_all_templates_have_tags(self):
        for tmpl in template_registry.list_templates():
            assert len(tmpl.tags) > 0, f"Template '{tmpl.template_id}' has no tags"
