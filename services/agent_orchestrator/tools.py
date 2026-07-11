"""Tool Registry and execution sandbox for agent tools."""

import asyncio
import inspect
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str  # "string", "integer", "number", "boolean", "array", "object"
    description: str
    required: bool = False
    default: Any = None
    enum: list[Any] | None = None
    properties: dict[str, "ToolParameter"] | None = None  # for object types


@dataclass
class ToolDefinition:
    """Definition of a tool."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    returns: str | None = None
    category: str = "general"
    requires_approval: bool = False
    timeout_seconds: int = 30
    rate_limit: int | None = None  # calls per minute
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Base class for all tools."""

    def __init__(self, definition: ToolDefinition):
        self.definition = definition
        self._call_count = 0
        self._last_call_time = 0.0

    @property
    def name(self) -> str:
        return self.definition.name

    @abstractmethod
    async def execute(self, **params) -> Any:
        """Execute the tool with given parameters."""
        pass

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate parameters against tool definition."""
        for param_def in self.definition.parameters:
            if param_def.required and param_def.name not in params:
                return False, f"Required parameter '{param_def.name}' missing"

            if param_def.name in params:
                value = params[param_def.name]
                if not self._validate_type(value, param_def):
                    return False, f"Parameter '{param_def.name}' has invalid type"

                if param_def.enum and value not in param_def.enum:
                    return False, f"Parameter '{param_def.name}' must be one of {param_def.enum}"

        return True, None

    def _validate_type(self, value: Any, param_def: ToolParameter) -> bool:
        """Validate a value against a parameter type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_type = type_map.get(param_def.type)
        if expected_type is None:
            return True  # Unknown type, allow

        if isinstance(expected_type, tuple):
            return isinstance(value, expected_type)
        return isinstance(value, expected_type)

    def to_openai_function(self) -> dict[str, Any]:
        """Convert tool definition to OpenAI function format."""
        properties = {}
        required = []

        for param in self.definition.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            if param.properties:
                prop["properties"] = {
                    k: {"type": v.type, "description": v.description}
                    for k, v in param.properties.items()
                }
                prop["type"] = "object"

            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.definition.name,
                "description": self.definition.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._categories: dict[str, list[str]] = {}
        _registry_lock: asyncio.Lock = asyncio.Lock()

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self.tools:
            logger.warning("Overwriting existing tool: %s", tool.name)

        self.tools[tool.name] = tool

        category = tool.definition.category
        if category not in self._categories:
            self._categories[category] = []
        if tool.name not in self._categories[category]:
            self._categories[category].append(tool.name)

        logger.info("Registered tool: %s (%s)", tool.name, category)

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool."""
        tool = self.tools.pop(tool_name, None)
        if tool:
            for cat_tools in self._categories.values():
                if tool_name in cat_tools:
                    cat_tools.remove(tool_name)
            logger.info("Unregistered tool: %s", tool_name)
            return True
        return False

    def get_tool(self, tool_name: str) -> Tool | None:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[Tool]:
        """Get all tools in a category."""
        return [self.tools[name] for name in self._categories.get(category, [])]

    def list_tools(self) -> list[ToolDefinition]:
        """List all tool definitions."""
        return [tool.definition for tool in self.tools.values()]

    def list_categories(self) -> list[str]:
        """List all categories."""
        return list(self._categories.keys())

    def get_tool_openai_functions(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI function format."""
        return [tool.to_openai_function() for tool in self.tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: "AgentContext | None" = None,
    ) -> dict[str, Any]:
        """Execute a tool with validation and monitoring."""
        tool = self.tools.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool_name": tool_name,
            }

        # Check rate limit
        if tool.definition.rate_limit:
            now = time.time()
            if now - tool._last_call_time < 60 / tool.definition.rate_limit:
                return {
                    "success": False,
                    "error": f"Rate limit exceeded for tool '{tool_name}'",
                    "tool_name": tool_name,
                }
            tool._last_call_time = now

        # Validate parameters
        valid, error = tool.validate_params(params)
        if not valid:
            return {
                "success": False,
                "error": error,
                "tool_name": tool_name,
            }

        # Execute with timeout
        try:
            tool._call_count += 1
            result = await asyncio.wait_for(
                tool.execute(**params, context=context),
                timeout=tool.definition.timeout_seconds,
            )
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' timed out after {tool.definition.timeout_seconds}s",
                "tool_name": tool_name,
            }
        except Exception as e:
            logger.exception("Tool execution failed: %s", tool_name)
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
            }


class ExecutionSandbox:
    """Sandbox for executing code and commands safely."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_memory_mb: int = 512,
        allowed_imports: list[str] | None = None,
        blocked_imports: list[str] | None = None,
        allow_network: bool = False,
        allow_filesystem: bool = False,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.allowed_imports = set(allowed_imports or [
            "json", "re", "math", "random", "datetime", "itertools",
            "collections", "statistics", "hashlib", "base64", "uuid",
        ])
        self.blocked_imports = set(blocked_imports or [
            "os", "sys", "subprocess", "socket", "requests",
            "urllib", "http", "ftplib", "smtplib", "pickle",
            "marshal", "importlib", "pkgutil", "runpy",
        ])
        self.allow_network = allow_network
        self.allow_filesystem = allow_filesystem

    def validate_code(self, code: str) -> tuple[bool, str | None]:
        """Validate code for safety."""
        # Check for blocked imports
        import_pattern = r"^\s*(import|from)\s+(\w+)"
        for line in code.split("\n"):
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                parts = line.split()
                if len(parts) >= 2:
                    module = parts[1].split(".")[0]
                    if module in self.blocked_imports:
                        return False, f"Import of '{module}' is not allowed"
                    if module not in self.allowed_imports and not self._is_stdlib_safe(module):
                        return False, f"Import of '{module}' is not in allowed list"

        # Check for dangerous patterns
        dangerous_patterns = [
            "eval(", "exec(", "compile(", "__import__(",
            "open(", "os.", "sys.", "subprocess.",
            "socket.", "requests.", "urllib.",
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"

        return True, None

    def _is_stdlib_safe(self, module: str) -> bool:
        """Check if a standard library module is safe."""
        safe_modules = {
            "json", "re", "math", "random", "datetime", "itertools",
            "collections", "statistics", "hashlib", "base64", "uuid",
            "decimal", "fractions", "typing", "dataclasses", "enum",
            "string", "textwrap", "unicodedata", "copy", "pprint",
        }
        return module in safe_modules

    async def execute_python(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute Python code in sandbox."""
        # Validate code
        valid, error = self.validate_code(code)
        if not valid:
            return {"success": False, "error": error}

        # Prepare restricted globals
        safe_globals = {
            "__builtins__": {
                "len": len, "str": str, "int": int, "float": float,
                "bool": bool, "list": list, "dict": dict, "set": set,
                "tuple": tuple, "range": range, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter, "sum": sum,
                "min": min, "max": max, "abs": abs, "round": round,
                "sorted": sorted, "reversed": reversed, "any": any,
                "all": all, "isinstance": isinstance, "hasattr": hasattr,
                "getattr": getattr, "setattr": setattr, "type": type,
                "print": print, "Exception": Exception, "ValueError": ValueError,
                "TypeError": TypeError, "KeyError": KeyError,
            },
        }

        if globals_dict:
            safe_globals.update(globals_dict)

        # Add allowed imports
        for module_name in self.allowed_imports:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass

        try:
            # Compile and execute
            compiled = compile(code, "<sandbox>", "exec")
            local_vars = {}

            await asyncio.wait_for(
                asyncio.to_thread(exec, compiled, safe_globals, local_vars),
                timeout=self.timeout_seconds,
            )

            return {
                "success": True,
                "result": local_vars,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Execution timed out after {self.timeout_seconds}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_command(
        self,
        command: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute a shell command (if allowed)."""
        if not self.allow_filesystem:
            return {"success": False, "error": "Filesystem access not allowed"}

        # Only allow specific safe commands
        allowed_commands = {"ls", "cat", "head", "tail", "grep", "wc", "find", "which"}
        if command[0] not in allowed_commands:
            return {"success": False, "error": f"Command '{command[0]}' not allowed"}

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": process.returncode,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instances
tool_registry = ToolRegistry()
default_sandbox = ExecutionSandbox()