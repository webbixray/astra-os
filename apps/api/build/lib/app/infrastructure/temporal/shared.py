"""Shared data objects for Temporal workflows."""

from dataclasses import dataclass


@dataclass
class CompileWorkflowInput:
    workflow_id: str
    organization_id: str
    name: str
    nodes: list[dict]
    edges: list[dict]


@dataclass
class ExecuteStepInput:
    step_id: str
    label: str
    node_type: str
    config: dict
    context: dict


@dataclass
class StepResult:
    success: bool = True
    result: dict | None = None
    error: str = ""
