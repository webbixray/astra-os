"""Workflow Templates — Pre-built templates for common marketing workflows.

M5 Workflow Engine: Provides ready-to-use workflow templates that users
can instantiate and customize for their specific needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.workflows.workflow import (
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
)


@dataclass
class WorkflowTemplate:
    """A pre-built workflow template."""

    template_id: str
    name: str
    description: str
    category: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    estimated_duration_minutes: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "tags": self.tags,
        }

    def instantiate(
        self,
        organization_id: UUID,
        created_by: UUID,
        name: str | None = None,
    ) -> Workflow:
        """Create a Workflow instance from this template."""
        return Workflow.create(
            organization_id=organization_id,
            name=name or self.name,
            created_by=created_by,
            description=self.description,
        ).__class__(
            id=uuid4(),
            organization_id=organization_id,
            name=name or self.name,
            description=self.description,
            nodes=list(self.nodes),
            edges=list(self.edges),
            created_by=created_by,
        )


# ---------------------------------------------------------------------------
# Built-in Templates
# ---------------------------------------------------------------------------

def _campaign_launch_template() -> WorkflowTemplate:
    """Campaign Launch — create, review, approve, launch, monitor."""
    return WorkflowTemplate(
        template_id="campaign_launch",
        name="Campaign Launch",
        description="Standard campaign launch workflow: create content → review → approve → launch → monitor performance.",
        category="campaign",
        estimated_duration_minutes=120,
        tags=["campaign", "launch", "approval"],
        nodes=[
            WorkflowNode.create("t1", NodeType.TRIGGER, "Campaign Created",
                                position_x=250, position_y=0),
            WorkflowNode.create("a1", NodeType.ACTION, "Generate Content",
                                {"action_type": "content.generate", "agent_type": "ContentSpecialist"},
                                position_x=250, position_y=80),
            WorkflowNode.create("c1", NodeType.CONDITION, "Content Approved?",
                                {"condition": "content.status == 'approved'"},
                                position_x=250, position_y=160),
            WorkflowNode.create("ap1", NodeType.APPROVAL, "Manager Review",
                                {"approver_role": "marketing_director", "timeout_hours": 24},
                                position_x=450, position_y=160),
            WorkflowNode.create("a2", NodeType.ACTION, "Launch Campaign",
                                {"action_type": "campaign.launch"},
                                position_x=250, position_y=240),
            WorkflowNode.create("d1", NodeType.DELAY, "Wait 24h",
                                {"seconds": 86400},
                                position_x=250, position_y=320),
            WorkflowNode.create("a3", NodeType.ACTION, "Check Performance",
                                {"action_type": "analytics.report"},
                                position_x=250, position_y=400),
            WorkflowNode.create("e1", NodeType.END, "Complete",
                                position_x=250, position_y=480),
        ],
        edges=[
            WorkflowEdge.create("e1", "t1", "a1"),
            WorkflowEdge.create("e2", "a1", "c1"),
            WorkflowEdge.create("e3", "c1", "a2", "yes"),
            WorkflowEdge.create("e4", "c1", "ap1", "no"),
            WorkflowEdge.create("e5", "ap1", "a2"),
            WorkflowEdge.create("e6", "a2", "d1"),
            WorkflowEdge.create("e7", "d1", "a3"),
            WorkflowEdge.create("e8", "a3", "e1"),
        ],
    )


def _creative_review_template() -> WorkflowTemplate:
    """Creative Review — generate → review → approve/reject → iterate."""
    return WorkflowTemplate(
        template_id="creative_review",
        name="Creative Review",
        description="Creative asset review workflow with approval gates and revision cycles.",
        category="content",
        estimated_duration_minutes=60,
        tags=["creative", "review", "approval"],
        nodes=[
            WorkflowNode.create("t1", NodeType.TRIGGER, "Review Requested",
                                position_x=250, position_y=0),
            WorkflowNode.create("a1", NodeType.ACTION, "AI Content Review",
                                {"action_type": "content.review", "agent_type": "ContentReviewer"},
                                position_x=250, position_y=80),
            WorkflowNode.create("ap1", NodeType.APPROVAL, "Creative Director Review",
                                {"approver_role": "creative_director", "timeout_hours": 48},
                                position_x=250, position_y=160),
            WorkflowNode.create("c1", NodeType.CONDITION, "Approved?",
                                {"condition": "approval.status == 'approved'"},
                                position_x=250, position_y=240),
            WorkflowNode.create("a2", NodeType.ACTION, "Publish Asset",
                                {"action_type": "content.publish"},
                                position_x=100, position_y=320),
            WorkflowNode.create("a3", NodeType.ACTION, "Request Revision",
                                {"action_type": "content.revise"},
                                position_x=400, position_y=320),
            WorkflowNode.create("e1", NodeType.END, "Complete",
                                position_x=250, position_y=400),
        ],
        edges=[
            WorkflowEdge.create("e1", "t1", "a1"),
            WorkflowEdge.create("e2", "a1", "ap1"),
            WorkflowEdge.create("e3", "ap1", "c1"),
            WorkflowEdge.create("e4", "c1", "a2", "yes"),
            WorkflowEdge.create("e5", "c1", "a3", "no"),
            WorkflowEdge.create("e6", "a2", "e1"),
            WorkflowEdge.create("e7", "a3", "a1"),
        ],
    )


def _optimization_loop_template() -> WorkflowTemplate:
    """Optimization Loop — monitor → analyze → optimize → repeat."""
    return WorkflowTemplate(
        template_id="optimization_loop",
        name="Optimization Loop",
        description="Continuous optimization: monitor performance, analyze patterns, apply optimizations.",
        category="optimization",
        estimated_duration_minutes=480,
        tags=["optimization", "monitoring", "loop"],
        nodes=[
            WorkflowNode.create("t1", NodeType.TRIGGER, "Scheduled (Daily)",
                                {"trigger_type": "cron", "cron": "0 9 * * *"},
                                position_x=250, position_y=0),
            WorkflowNode.create("a1", NodeType.ACTION, "Collect Metrics",
                                {"action_type": "analytics.collect"},
                                position_x=250, position_y=80),
            WorkflowNode.create("a2", NodeType.ACTION, "Analyze Performance",
                                {"action_type": "analytics.analyze", "agent_type": "DataAnalyst"},
                                position_x=250, position_y=160),
            WorkflowNode.create("c1", NodeType.CONDITION, "Needs Optimization?",
                                {"condition": "analysis.roas < 3.0"},
                                position_x=250, position_y=240),
            WorkflowNode.create("a3", NodeType.ACTION, "Apply Optimizations",
                                {"action_type": "campaign.optimize", "agent_type": "CampaignOptimizer"},
                                position_x=100, position_y=320),
            WorkflowNode.create("a4", NodeType.ACTION, "Generate Report",
                                {"action_type": "report.generate"},
                                position_x=400, position_y=320),
            WorkflowNode.create("d1", NodeType.DELAY, "Wait Until Tomorrow",
                                {"seconds": 86400},
                                position_x=250, position_y=400),
            WorkflowNode.create("e1", NodeType.END, "Cycle Complete",
                                position_x=250, position_y=480),
        ],
        edges=[
            WorkflowEdge.create("e1", "t1", "a1"),
            WorkflowEdge.create("e2", "a1", "a2"),
            WorkflowEdge.create("e3", "a2", "c1"),
            WorkflowEdge.create("e4", "c1", "a3", "yes"),
            WorkflowEdge.create("e5", "c1", "a4", "no"),
            WorkflowEdge.create("e6", "a3", "d1"),
            WorkflowEdge.create("e7", "a4", "d1"),
            WorkflowEdge.create("e8", "d1", "e1"),
        ],
    )


def _brand_compliance_template() -> WorkflowTemplate:
    """Brand Compliance Check — content → brand audit → approve/reject."""
    return WorkflowTemplate(
        template_id="brand_compliance",
        name="Brand Compliance Check",
        description="Automated brand compliance: check content against brand guidelines with human review.",
        category="compliance",
        estimated_duration_minutes=30,
        tags=["brand", "compliance", "approval"],
        nodes=[
            WorkflowNode.create("t1", NodeType.TRIGGER, "Content Submitted",
                                position_x=250, position_y=0),
            WorkflowNode.create("a1", NodeType.ACTION, "Brand Voice Check",
                                {"action_type": "brand.check", "agent_type": "BrandVoice"},
                                position_x=250, position_y=80),
            WorkflowNode.create("a2", NodeType.ACTION, "Visual Compliance",
                                {"action_type": "brand.visual_check"},
                                position_x=250, position_y=160),
            WorkflowNode.create("c1", NodeType.CONDITION, "Compliant?",
                                {"condition": "brand_score >= 0.8"},
                                position_x=250, position_y=240),
            WorkflowNode.create("a3", NodeType.ACTION, "Approve Content",
                                {"action_type": "content.approve"},
                                position_x=100, position_y=320),
            WorkflowNode.create("a4", NodeType.ACTION, "Flag for Revision",
                                {"action_type": "content.flag"},
                                position_x=400, position_y=320),
            WorkflowNode.create("e1", NodeType.END, "Complete",
                                position_x=250, position_y=400),
        ],
        edges=[
            WorkflowEdge.create("e1", "t1", "a1"),
            WorkflowEdge.create("e2", "a1", "a2"),
            WorkflowEdge.create("e3", "a2", "c1"),
            WorkflowEdge.create("e4", "c1", "a3", "yes"),
            WorkflowEdge.create("e5", "c1", "a4", "no"),
            WorkflowEdge.create("e6", "a3", "e1"),
            WorkflowEdge.create("e7", "a4", "e1"),
        ],
    )


# ---------------------------------------------------------------------------
# Template Registry
# ---------------------------------------------------------------------------

_BUILTIN_TEMPLATES: list[WorkflowTemplate] = [
    _campaign_launch_template(),
    _creative_review_template(),
    _optimization_loop_template(),
    _brand_compliance_template(),
]


class WorkflowTemplateRegistry:
    """Registry of available workflow templates."""

    def __init__(self) -> None:
        self._templates: dict[str, WorkflowTemplate] = {}
        for t in _BUILTIN_TEMPLATES:
            self._templates[t.template_id] = t

    def list_templates(
        self,
        category: str | None = None,
    ) -> list[WorkflowTemplate]:
        """List all available templates, optionally filtered by category."""
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def get_template(self, template_id: str) -> WorkflowTemplate | None:
        """Get a specific template by ID."""
        return self._templates.get(template_id)

    def register_template(self, template: WorkflowTemplate) -> None:
        """Register a custom template."""
        self._templates[template.template_id] = template

    def instantiate_template(
        self,
        template_id: str,
        organization_id: UUID,
        created_by: UUID,
        name: str | None = None,
    ) -> Workflow | None:
        """Instantiate a template as a new workflow."""
        template = self.get_template(template_id)
        if template is None:
            return None
        return template.instantiate(
            organization_id=organization_id,
            created_by=created_by,
            name=name,
        )


# Singleton
template_registry = WorkflowTemplateRegistry()
