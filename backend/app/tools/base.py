"""
MR.GREEN — Base Tool Interface

Defines the standardized interface that all tools must implement.
Every tool is self-describing (name, description, schema, permissions)
and independently executable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for all MR.GREEN tools.

    Every tool must define:
    - name: Unique identifier
    - description: What the tool does (used by the AI to decide when to use it)
    - input_schema: JSON Schema describing expected input
    - permissions: Required permissions to execute

    And implement:
    - execute(): The actual tool logic
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for the tool's input parameters."""
        ...

    @property
    def permissions(self) -> list[str]:
        """List of permissions required to use this tool."""
        return []

    @property
    def requires_approval(self) -> bool:
        """Whether this tool requires explicit user approval before execution."""
        return False

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters matching the input_schema.

        Returns:
            ToolResult with success status, output, and optional error.
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize the tool's metadata for API responses and AI context."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "permissions": self.permissions,
            "requires_approval": self.requires_approval,
        }
