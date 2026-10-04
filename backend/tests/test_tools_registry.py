"""
Tests for ToolRegistry and ToolManifest validation.
"""

import pytest
from app.tools.base import BaseTool, ToolResult
from app.tools.manifest import RiskLevel, ToolManifest
from app.tools.registry import ToolRegistry


class DummyTool(BaseTool):
    def __init__(self, name: str = "dummy_tool", enabled: bool = True):
        self._name = name
        self._enabled = enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "A test dummy tool"

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    @property
    def permissions(self) -> list[str]:
        return ["filesystem.read"]

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="ok")


def test_manifest_validation():
    """Test valid and invalid tool manifests."""
    manifest = ToolManifest(
        name="web_search",
        version="1.0.0",
        description="Search the internet",
        category="research",
        permissions=["network.read"],
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        enabled=True,
    )
    assert manifest.name == "web_search"
    assert manifest.risk_level == RiskLevel.LOW

    # Invalid name
    with pytest.raises(ValueError):
        ToolManifest(name="", description="empty name")

    # Invalid risk level
    with pytest.raises(ValueError):
        ToolManifest(name="tool", description="desc", risk_level="extreme")


def test_registry_register_and_get():
    """Test registering and retrieving tools."""
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    assert registry.get("dummy_tool") is tool
    assert "dummy_tool" in registry.list_names()
    assert len(registry.list_all()) == 1


def test_registry_duplicate_prevention():
    """Test duplicate registration behavior."""
    registry = ToolRegistry()
    tool1 = DummyTool("tool1")
    tool2 = DummyTool("tool1")

    registry.register(tool1)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool2, overwrite=False)

    # Overwrite allowed when explicit
    registry.register(tool2, overwrite=True)
    assert registry.get("tool1") is tool2


def test_registry_enable_disable():
    """Test enabling and disabling tools."""
    registry = ToolRegistry()
    tool = DummyTool("toggle_tool")
    registry.register(tool)

    assert registry.is_enabled("toggle_tool") is True
    registry.disable("toggle_tool")
    assert registry.is_enabled("toggle_tool") is False
    assert len(registry.list_enabled()) == 0

    registry.enable("toggle_tool")
    assert registry.is_enabled("toggle_tool") is True
    assert len(registry.list_enabled()) == 1


def test_registry_unregister():
    """Test removing a tool from the registry."""
    registry = ToolRegistry()
    tool = DummyTool("temp_tool")
    registry.register(tool)
    assert registry.get("temp_tool") is not None

    registry.unregister("temp_tool")
    assert registry.get("temp_tool") is None
    assert "temp_tool" not in registry.list_names()


def test_registry_discover_builtins():
    """Test that all 6 builtins are properly loaded."""
    registry = ToolRegistry()
    registry.discover_builtins()

    expected = {"calculator", "time", "file_read", "file_write", "web_fetch", "shell"}
    registered_names = set(registry.list_names())
    assert expected.issubset(registered_names)

    # Shell must be disabled by default
    assert registry.is_enabled("shell") is False
    # Calculator must be enabled by default
    assert registry.is_enabled("calculator") is True
