"""
MR.GREEN — Planner

Analyzes user requests and formulates action plans:
- Direct conversation (no tools)
- Tool invocation (calculator, time, file_read, file_write, web_fetch, shell)
- Multi-step reasoning
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

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
    tool_args: dict[str, Any] | None = None


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

    @property
    def has_tool_calls(self) -> bool:
        return any(a.action_type == ActionType.TOOL_CALL for a in self.actions)


class Planner:
    """
    Determines optimal execution strategy for user messages.
    Routes queries to specialized tools when applicable, or direct AI conversation.
    """

    async def plan(
        self,
        user_message: str,
        available_tools: list[str] | None = None,
    ) -> Plan:
        """
        Analyze user message and formulate an action plan.
        """
        tools = set(available_tools or [])
        clean_msg = user_message.strip()
        lower_msg = clean_msg.lower()

        # 1. Check for Calculation intent
        if "calculator" in tools:
            math_match = self._detect_calculation(clean_msg)
            if math_match:
                logger.info("Planner selected calculator tool for: %s", math_match)
                return Plan(
                    actions=[
                        PlannedAction(
                            action_type=ActionType.TOOL_CALL,
                            description=f"Calculate mathematical expression: {math_match}",
                            tool_name="calculator",
                            tool_args={"expression": math_match},
                        )
                    ],
                    reasoning=f"Identified mathematical computation request: '{math_match}'",
                )

        # 2. Check for Time / Date intent
        if "time" in tools:
            if self._detect_time_query(lower_msg):
                logger.info("Planner selected time tool for query: %s", lower_msg)
                return Plan(
                    actions=[
                        PlannedAction(
                            action_type=ActionType.TOOL_CALL,
                            description="Retrieve current date and time",
                            tool_name="time",
                            tool_args={"timezone": "UTC"},
                        )
                    ],
                    reasoning="User requested current temporal or time information.",
                )

        # 3. Check for Web Fetch intent
        if "web_fetch" in tools:
            url = self._extract_url(clean_msg)
            if url and any(keyword in lower_msg for keyword in ("fetch", "check", "scrape", "get", "summarize", "read", "http")):
                logger.info("Planner selected web_fetch tool for URL: %s", url)
                return Plan(
                    actions=[
                        PlannedAction(
                            action_type=ActionType.TOOL_CALL,
                            description=f"Fetch public web page: {url}",
                            tool_name="web_fetch",
                            tool_args={"url": url},
                        )
                    ],
                    reasoning=f"Request contains URL and reading intent: '{url}'",
                )

        # 4. Check for File Read intent
        if "file_read" in tools:
            file_path = self._detect_file_read(clean_msg)
            if file_path:
                logger.info("Planner selected file_read tool for path: %s", file_path)
                return Plan(
                    actions=[
                        PlannedAction(
                            action_type=ActionType.TOOL_CALL,
                            description=f"Read workspace file: {file_path}",
                            tool_name="file_read",
                            tool_args={"path": file_path},
                        )
                    ],
                    reasoning=f"Request asks to read file '{file_path}'",
                )

        # Default: Direct Conversational Response
        return Plan(
            actions=[
                PlannedAction(
                    action_type=ActionType.RESPOND,
                    description="Generate direct conversational response",
                )
            ],
            reasoning="Standard conversational query — answer directly without tools",
        )

    def _detect_calculation(self, text: str) -> str | None:
        """Detect mathematical expression in text."""
        # e.g., "Calculate 125 * 48", "what is 25 * 4", "compute 50 / 2", "125 * 48"
        pattern = r"(?:calculate|compute|what is|evaluate)?\s*([0-9\.\s\+\-\*\/\(\)\^\%]+(?:sqrt|sin|cos|tan|pi|e)?.*)$"
        # Check explicit calculate prefix
        calc_prefix = re.search(r"(?:calculate|compute|evaluate|what is)\s+([0-9\.\s\+\-\*\/\(\)\^\%]+)", text, re.IGNORECASE)
        if calc_prefix:
            expr = calc_prefix.group(1).strip().rstrip("?")
            if any(op in expr for op in ("+", "-", "*", "/", "%", "^")):
                return expr

        # Check pure math expression (e.g. "25 * 4", "100 + 50")
        pure_math = re.match(r"^\s*([0-9\.]+\s*[\+\-\*\/]\s*[0-9\.]+(?:\s*[\+\-\*\/]\s*[0-9\.]+)*)\s*\??$", text)
        if pure_math:
            return pure_math.group(1).strip()

        return None

    def _detect_time_query(self, lower: str) -> bool:
        """Detect if the user is asking for the current time or date."""
        time_triggers = [
            "what time is it",
            "current time",
            "tell me the time",
            "what's the time",
            "what date is it",
            "today's date",
            "what is today's date",
            "current date",
        ]
        return any(trigger in lower for trigger in time_triggers)

    def _extract_url(self, text: str) -> str | None:
        """Extract first HTTP/HTTPS URL from text."""
        match = re.search(r"https?://[^\s<>\"']+", text)
        return match.group(0) if match else None

    def _detect_file_read(self, text: str) -> str | None:
        """Detect file read command."""
        match = re.search(r"(?:read\s+file|read|open|view\s+file)\s+([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
