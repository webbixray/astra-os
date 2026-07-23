from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class ToolCategory(str, Enum):
    CAMPAIGN = "campaign"
    CONTENT = "content"
    ANALYTICS = "analytics"
    WORKFLOW = "workflow"
    COMMUNICATION = "communication"


@dataclass
class Tool:
    name: str
    description: str
    category: ToolCategory
    handler: Callable[..., Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)

    async def execute(self, **kwargs: Any) -> Any:
        if self.handler is None:
            return {"error": f"Tool '{self.name}' has no handler registered"}
        return await self.handler(**kwargs)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_by_category(self, category: ToolCategory) -> list[Tool]:
        return [t for t in self._tools.values() if t.category == category]

    def list_all(self) -> list[Tool]:
        return list(self._tools.values())

    def get_capability_descriptions(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]
