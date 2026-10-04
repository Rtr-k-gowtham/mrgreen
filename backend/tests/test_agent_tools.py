"""
Tests for Agent Planner tool routing.
"""

import pytest
from app.agent.planner import ActionType, Planner


@pytest.mark.asyncio
async def test_planner_direct_conversation():
    """Test standard conversational queries plan direct responses."""
    planner = Planner()
    plan = await planner.plan("Hello MR.GREEN, how are you?", available_tools=["calculator", "time"])
    assert plan.is_simple_response is True
    assert plan.actions[0].action_type == ActionType.RESPOND


@pytest.mark.asyncio
async def test_planner_routes_to_calculator():
    """Test math expressions route to calculator tool."""
    planner = Planner()
    plan = await planner.plan("Calculate 125 * 48", available_tools=["calculator", "time"])
    assert plan.has_tool_calls is True
    assert plan.actions[0].tool_name == "calculator"
    assert "125 * 48" in plan.actions[0].tool_args["expression"]


@pytest.mark.asyncio
async def test_planner_routes_to_time():
    """Test time queries route to time tool."""
    planner = Planner()
    plan = await planner.plan("What time is it right now?", available_tools=["calculator", "time"])
    assert plan.has_tool_calls is True
    assert plan.actions[0].tool_name == "time"


@pytest.mark.asyncio
async def test_planner_routes_to_web_fetch():
    """Test web fetch queries route to web_fetch tool."""
    planner = Planner()
    plan = await planner.plan("Fetch https://example.com/docs", available_tools=["web_fetch", "calculator"])
    assert plan.has_tool_calls is True
    assert plan.actions[0].tool_name == "web_fetch"
    assert plan.actions[0].tool_args["url"] == "https://example.com/docs"
