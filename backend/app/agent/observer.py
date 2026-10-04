"""
MR.GREEN — Observer

Observes and interprets the results of tool executions and AI responses.
Determines whether the result is satisfactory or requires replanning.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Observation:
    """Result of observing an action's outcome."""
    success: bool
    summary: str
    should_continue: bool = False
    error: str | None = None


class Observer:
    """
    Observes the results of agent actions.

    For Milestone 1: Simple pass-through observation.
    Future: Will analyze tool outputs, detect errors, and suggest replanning.
    """

    async def observe_response(self, response_content: str) -> Observation:
        """Observe an AI-generated response."""
        if not response_content or not response_content.strip():
            return Observation(
                success=False,
                summary="Empty response received",
                should_continue=True,
                error="AI returned an empty response",
            )

        return Observation(
            success=True,
            summary="Response generated successfully",
        )

    async def observe_tool_result(
        self,
        tool_name: str,
        success: bool,
        output: str | None = None,
        error: str | None = None,
    ) -> Observation:
        """Observe a tool execution result."""
        if success:
            return Observation(
                success=True,
                summary=f"Tool '{tool_name}' completed successfully",
            )
        else:
            return Observation(
                success=False,
                summary=f"Tool '{tool_name}' failed",
                should_continue=True,  # Allow replanning
                error=error,
            )
