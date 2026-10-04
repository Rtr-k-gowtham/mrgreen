"""
Tests for ToolExecutor lifecycle and safety gating.
"""

import pytest
from app.tools.base import BaseTool, ToolResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


class TestTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "Mock tool for executor tests"

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    async def execute(self, **kwargs) -> ToolResult:
        if kwargs.get("fail"):
            return ToolResult(success=False, error="Intentional failure")
        return ToolResult(success=True, output={"msg": "success"})


class CriticalMockTool(BaseTool):
    @property
    def name(self) -> str:
        return "critical_tool"

    @property
    def description(self) -> str:
        return "Requires approval"

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    @property
    def risk_level(self) -> str:
        return "critical"

    @property
    def requires_approval(self) -> bool:
        return True

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="critical done")


@pytest.mark.asyncio
async def test_executor_success():
    """Test standard successful tool execution."""
    reg = ToolRegistry()
    reg.register(TestTool())
    executor = ToolExecutor(registry=reg)

    res = await executor.execute("mock_tool", arguments={})
    assert res.success is True
    assert res.status == "completed"
    assert res.result == {"msg": "success"}


@pytest.mark.asyncio
async def test_executor_unknown_tool():
    """Test executing a non-existent tool."""
    reg = ToolRegistry()
    executor = ToolExecutor(registry=reg)

    res = await executor.execute("ghost_tool")
    assert res.success is False
    assert "not found" in res.error.lower()


@pytest.mark.asyncio
async def test_executor_disabled_tool():
    """Test executing a disabled tool."""
    reg = ToolRegistry()
    reg.register(TestTool())
    reg.disable("mock_tool")
    executor = ToolExecutor(registry=reg)

    res = await executor.execute("mock_tool")
    assert res.success is False
    assert "disabled" in res.error.lower()


@pytest.mark.asyncio
async def test_executor_approval_gating():
    """Test that critical tools require human approval when not pre-approved."""
    reg = ToolRegistry()
    reg.register(CriticalMockTool())
    executor = ToolExecutor(registry=reg)

    # Without pre-approval
    res = await executor.execute("critical_tool")
    assert res.success is False
    assert res.status == "pending_approval"
    assert "approval" in res.error.lower()

    # With pre-approval
    approved_res = await executor.execute("critical_tool", is_pre_approved=True)
    assert approved_res.success is True
    assert approved_res.result == "critical done"
