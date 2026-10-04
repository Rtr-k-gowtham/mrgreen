"""
MR.GREEN — Tool Manifest Schema

Defines and validates standard tool manifests.
Every tool in MR.GREEN conforms to this specification.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Supported risk levels for tools and capabilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolManifest(BaseModel):
    """
    Standard declarative specification for a MR.GREEN tool.
    """
    name: str = Field(..., description="Unique tool name (snake_case, lowercase)")
    version: str = Field(default="1.0.0", description="Semantic version string")
    description: str = Field(..., description="Clear explanation of tool purpose and usage")
    category: str = Field(default="general", description="Tool category e.g. utility, filesystem, network")
    permissions: list[str] = Field(default_factory=list, description="Required system permissions")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Assessed risk level")
    requires_approval: bool = Field(default=False, description="Whether human approval is mandatory")
    enabled: bool = Field(default=True, description="Whether tool is enabled by default")
    input_schema: dict[str, Any] = Field(default_factory=dict, description="JSON Schema for inputs")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean:
            raise ValueError("Tool name cannot be empty")
        if not all(c.isalnum() or c in ("_", "-") for c in clean):
            raise ValueError(f"Invalid tool name '{v}'. Use letters, numbers, hyphens or underscores.")
        return clean

    @field_validator("risk_level", mode="before")
    @classmethod
    def normalize_risk_level(cls, v: Any) -> RiskLevel:
        if isinstance(v, RiskLevel):
            return v
        if isinstance(v, str):
            v_lower = v.strip().lower()
            try:
                return RiskLevel(v_lower)
            except ValueError:
                raise ValueError(f"Invalid risk_level '{v}'. Supported: low, medium, high, critical.")
        return RiskLevel.LOW

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to serializable dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "permissions": self.permissions,
            "risk_level": self.risk_level.value,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled,
            "input_schema": self.input_schema,
        }
