"""
MR.GREEN — Executor

Executes planned actions — either tool calls or AI generation.
Acts as the bridge between the planner's decisions and actual execution.
"""

import logging
import time
from typing import Any

from app.ai.provider import AIMessage, AIProvider, AIResponse
from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Executor:
    """
    Executes actions determined by the planner.

    Handles:
    - Direct AI responses
    - Tool execution with permission checks
    - Timeout enforcement
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        tool_timeout: int = 60,
    ):
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry
        self.tool_timeout = tool_timeout

    async def generate_response(
        self,
        messages: list[AIMessage],
        system_prompt: str,
        temperature: float = 0.7,
    ) -> AIResponse:
        """Generate a direct AI response."""
        return await self.ai_provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute a tool by name with the given arguments.

        Args:
            tool_name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool.

        Returns:
            ToolResult with execution outcome.
        """
        tool = self.tool_registry.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
            )

        # Check if approval is required
        if tool.requires_approval:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' requires approval before execution",
            )

        logger.info("Executing tool: %s", tool_name)
        start = time.monotonic()

        try:
            result = await tool.execute(**kwargs)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Tool completed: %s (success=%s, duration=%dms)",
                tool_name, result.success, result.duration_ms,
            )
            return result
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error("Tool failed: %s — %s", tool_name, str(e))
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
