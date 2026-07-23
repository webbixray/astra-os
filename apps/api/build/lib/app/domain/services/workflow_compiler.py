from app.domain.entities.workflows.execution import ExecutionStep
from app.domain.entities.workflows.workflow import NodeType, Workflow


class CompiledStep:
    def __init__(
        self,
        order: int,
        node_id: str,
        node_type: NodeType,
        label: str,
        config: dict,
    ):
        self.order = order
        self.node_id = node_id
        self.node_type = node_type
        self.label = label
        self.config = config

    def to_execution_step(self) -> ExecutionStep:
        return ExecutionStep(
            id=f"step-{self.order}-{self.node_id}",
            node_id=self.node_id,
        )


class CompileError(Exception): ...


def compile_workflow(workflow: Workflow) -> list[CompiledStep]:
    if not workflow.nodes:
        raise CompileError("Workflow has no nodes")

    nodes_by_id = {n.id: n for n in workflow.nodes}
    edges_by_source: dict[str, list] = {}
    for edge in workflow.edges:
        if edge.source_id not in edges_by_source:
            edges_by_source[edge.source_id] = []
        edges_by_source[edge.source_id].append(edge)

    triggers = [n for n in workflow.nodes if n.type == NodeType.TRIGGER]
    if not triggers:
        raise CompileError("Workflow must have a trigger node")

    ordered_steps: list[CompiledStep] = []
    visited: set[str] = set()
    queue: list[str] = [triggers[0].id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        node = nodes_by_id.get(current_id)
        if not node:
            continue

        if node.type != NodeType.END:
            step = CompiledStep(
                order=len(ordered_steps),
                node_id=node.id,
                node_type=node.type,
                label=node.label,
                config=node.config,
            )
            ordered_steps.append(step)

        unvisited = [
            edge.target_id
            for edge in edges_by_source.get(current_id, [])
            if edge.target_id not in visited
        ]
        queue.extend(unvisited)

    return ordered_steps
