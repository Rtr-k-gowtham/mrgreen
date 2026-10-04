"""
MR.GREEN — Universal Base Tool Interface

Defines the standardized interface that all tools must implement.
Every tool is self-describing (name, description, schema, permissions, risk level)
and independently executable with safety checks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.tools.manifest import RiskLevel, ToolManifest


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary matching target specification."""
        return {
            "success": self.success,
            "result": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """
    Abstract base class for all MR.GREEN tools.

    Every tool must define:
    - name: Unique identifier
    - description: What the tool does (used by the AI to decide when to use it)
    - input_schema: JSON Schema describing expected input
    - permissions: Required permissions to execute
    - risk_level: Assessed risk level (low, medium, high, critical)
    - requires_approval: Whether explicit human approval is needed
    - enabled: Whether tool is active by default

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
    def version(self) -> str:
        """Semantic version of the tool."""
        return "1.0.0"

    @property
    def category(self) -> str:
        """Category of the tool."""
        return "general"

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
    def risk_level(self) -> str:
        """Assessed risk level: low, medium, high, critical."""
        return RiskLevel.LOW.value

    @property
    def requires_approval(self) -> bool:
        """Whether this tool requires explicit user approval before execution."""
        return self.risk_level in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)

    @property
    def enabled(self) -> bool:
        """Whether this tool is currently enabled."""
        return True

    @property
    def manifest(self) -> ToolManifest:
        """Generate manifest from tool properties."""
        return ToolManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            category=self.category,
            permissions=self.permissions,
            risk_level=RiskLevel(self.risk_level),
            requires_approval=self.requires_approval,
            enabled=self.enabled,
            input_schema=self.input_schema,
        )

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
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "input_schema": self.input_schema,
            "permissions": self.permissions,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled,
        }
