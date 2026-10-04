"""
MR.GREEN — Tool Registry

Central registry for discovering, registering, and looking up tools.
The agent queries this registry to find available tools dynamically.
"""

import logging
from typing import Any

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all available tools.

    Tools can be registered at startup (built-ins) or dynamically
    when new capabilities are added.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool: %s", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            logger.info("Unregistered tool: %s", name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tools_for_ai(self) -> list[dict[str, Any]]:
        """
        Get tool descriptions formatted for AI context.

        The AI uses these descriptions to decide which tools to invoke.
        """
        return [tool.to_dict() for tool in self._tools.values()]

    @property
    def count(self) -> int:
        return len(self._tools)


# Global tool registry instance
tool_registry = ToolRegistry()
