"""
MR.GREEN — Planner

Analyzes user requests and determines whether the agent should:
- Respond directly (simple conversation)
- Use a tool
- Execute a multi-step plan

For Milestone 1, the planner handles simple chat routing.
The full planning system (multi-step, tool selection) will be
built when the agent loop is expanded.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions the agent can take."""
    RESPOND = "respond"       # Direct AI response (no tools)
    TOOL_CALL = "tool_call"   # Use a specific tool
    MULTI_STEP = "multi_step" # Complex multi-step plan


@dataclass
class PlannedAction:
    """A single planned action."""
    action_type: ActionType
    description: str
    tool_name: str | None = None
    tool_args: dict | None = None


@dataclass
class Plan:
    """A plan consisting of one or more actions."""
    actions: list[PlannedAction]
    reasoning: str = ""

    @property
    def is_simple_response(self) -> bool:
        return (
            len(self.actions) == 1
            and self.actions[0].action_type == ActionType.RESPOND
        )


class Planner:
    """
    Determines what actions the agent should take for a given request.

    For Milestone 1: Always returns a simple RESPOND action.
    Future: Will analyze the request and plan tool calls / multi-step workflows.
    """

    async def plan(self, user_message: str, available_tools: list[str] | None = None) -> Plan:
        """
        Create a plan for responding to the user's message.

        Args:
            user_message: The user's input text.
            available_tools: List of tool names currently available.

        Returns:
            A Plan with one or more actions.
        """
        # Milestone 1: Simple response for all messages
        return Plan(
            actions=[
                PlannedAction(
                    action_type=ActionType.RESPOND,
                    description="Generate a direct response to the user",
                )
            ],
            reasoning="Simple conversation — direct response",
        )
