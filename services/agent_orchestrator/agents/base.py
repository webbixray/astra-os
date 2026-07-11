"""ReAct (Reason + Act) agent base implementation.

This module provides the core execution loop for all concrete agents.
The pattern: observe → think → act → observe → ... until done.
"""

import json
import logging
import time
from typing import Any

from ..agent import (
    Agent,
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentState,
    ToolCall,
    ToolResult,
)
from ..router import (
    ModelRequest,
    ModelResponse,
    get_model_router_facade,
)

logger = logging.getLogger(__name__)

# Default system prompt suffix for ReAct loop instructions
REACT_SYSTEM_SUFFIX = """

You operate using a structured reasoning and action loop.

When you receive a task, you must respond with a JSON object containing:
{{
  "thought": "Your reasoning about what to do next",
  "action": "tool_name or null if done",
  "action_input": {{"param": "value"}} or null,
  "final_answer": "your final response" or null
}}

Rules:
- Always include a "thought" explaining your reasoning
- If you need to use a tool, set "action" and "action_input"
- If you have enough information, set "final_answer" and set action to null
- You can use tools at most {max_tool_calls} times before providing a final answer
- Be concise and focused in your reasoning
"""


class ReActAgent(Agent):
    """Agent with ReAct (Reason + Act) execution loop.

    Subclasses should override `get_system_prompt()` and optionally
    `prepare_input()` / `process_output()` for domain-specific logic.
    """

    def __init__(
        self,
        config: AgentConfig,
        tenant_id: Any,
        **kwargs: Any,
    ):
        super().__init__(config=config, tenant_id=tenant_id, **kwargs)
        self._max_tool_calls = config.tool_config.get("max_tool_calls", 5)

    @property
    def system_prompt(self) -> str:
        """Build the full system prompt with ReAct instructions."""
        base = self.config.system_prompt or self.get_system_prompt()
        suffix = REACT_SYSTEM_SUFFIX.format(max_tool_calls=self._max_tool_calls)
        return f"{base}\n{suffix}"

    def get_system_prompt(self) -> str:
        """Override in subclasses to provide agent-specific system prompt."""
        return self.config.system_prompt or "You are a helpful AI agent."

    def prepare_input(self, input_data: Any) -> str:
        """Transform raw input_data into a prompt string for the LLM.

        Override for custom input preparation.
        """
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            return json.dumps(input_data, default=str)
        return str(input_data)

    def process_output(self, raw_output: str) -> Any:
        """Parse LLM output into structured response.

        Returns a dict with keys: thought, action, action_input, final_answer.
        Override for custom output processing.
        """
        # Try to extract JSON from the response
        text = raw_output.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            code_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    code_lines.append(line)
            text = "\n".join(code_lines)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # If not valid JSON, treat entire output as final answer
            parsed = {
                "thought": "Could not parse structured output",
                "action": None,
                "action_input": None,
                "final_answer": text,
            }

        # Ensure required keys exist
        return {
            "thought": parsed.get("thought", ""),
            "action": parsed.get("action"),
            "action_input": parsed.get("action_input") or {},
            "final_answer": parsed.get("final_answer"),
        }

    async def reason(self, context: AgentContext, observation: Any) -> Any:
        """Reason about the current observation and decide next action.

        Uses the model router to call an LLM with the current conversation
        history and the latest observation.
        """
        # Build messages for the LLM call
        messages = getattr(self, "_messages", [])
        if observation:
            messages.append({"role": "user", "content": str(observation)})

        # Get available tools as function definitions
        tools = self.get_available_tools()

        request = ModelRequest(
            messages=messages,
            system_prompt=self.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            tools=tools if tools else None,
        )

        router = get_model_router_facade()
        response: ModelResponse = await router.generate(request)

        # Track token usage
        usage = response.usage
        self._tokens_used += usage.get("total_tokens", 0)
        self._cost_usd += response.cost_usd

        # Store assistant response in conversation history
        messages.append({"role": "assistant", "content": response.content})
        self._messages = messages

        return response.content

    async def execute(self, context: AgentContext, input_data: Any) -> AgentResult:
        """Execute the ReAct loop: think → act → observe → repeat."""
        self._start_time = time.time()
        self._iteration = 0
        self._tool_calls = []
        self._tool_results = []
        self._messages = []

        prompt = self.prepare_input(input_data)
        observation = prompt
        final_answer = None

        try:
            for i in range(self.config.max_iterations):
                self._iteration = i + 1

                # Reason about current observation
                self.state = AgentState.RUNNING
                raw_output = await self.reason(context, observation)
                parsed = self.process_output(raw_output)

                logger.info(
                    "Agent %s iteration %d: thought=%s, action=%s",
                    self.agent_id,
                    self._iteration,
                    parsed["thought"][:100] if parsed["thought"] else "",
                    parsed["action"],
                )

                # Check if agent has a final answer
                if parsed.get("final_answer"):
                    final_answer = parsed["final_answer"]
                    break

                # Execute tool if action is specified
                action = parsed.get("action")
                if action:
                    action_input = parsed.get("action_input", {})
                    tool_result = await self.call_tool(action, action_input, context)
                    observation = (
                        f"Tool '{action}' result: {tool_result.result}"
                        if tool_result.success
                        else f"Tool '{action}' failed: {tool_result.error}"
                    )
                else:
                    # No action and no final answer — treat output as final
                    final_answer = raw_output
                    break
            else:
                # Max iterations reached
                final_answer = (
                    f"Max iterations ({self.config.max_iterations}) reached. "
                    f"Last reasoning: {parsed.get('thought', 'N/A')}"
                )

            return AgentResult(
                agent_id=self.agent_id,
                success=True,
                output=final_answer,
                tool_calls=self._tool_calls,
                tool_results=self._tool_results,
                tokens_used=self._tokens_used,
                cost_usd=self._cost_usd,
                duration_ms=int((time.time() - self._start_time) * 1000),
                iterations=self._iteration,
            )

        except Exception as e:
            logger.exception("ReAct agent %s failed at iteration %d", self.agent_id, self._iteration)
            return AgentResult(
                agent_id=self.agent_id,
                success=False,
                error=str(e),
                output=final_answer,
                tool_calls=self._tool_calls,
                tool_results=self._tool_results,
                tokens_used=self._tokens_used,
                cost_usd=self._cost_usd,
                duration_ms=int((time.time() - self._start_time) * 1000),
                iterations=self._iteration,
            )
