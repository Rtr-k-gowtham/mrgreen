"""
Tests for Safe Calculator Tool.
"""

import pytest
from app.tools.builtins.calculator.tool import CalculatorTool, evaluate_expression


@pytest.mark.asyncio
async def test_calculator_basic_arithmetic():
    """Test basic arithmetic operations."""
    tool = CalculatorTool()
    res = await tool.execute(expression="25 * 4")
    assert res.success is True
    assert res.output["result"] == 100

    res2 = await tool.execute(expression="125 * 48")
    assert res2.success is True
    assert res2.output["result"] == 6000

    res3 = await tool.execute(expression="10 + 5 * 2 - 4 / 2")
    assert res3.success is True
    assert res3.output["result"] == 18


@pytest.mark.asyncio
async def test_calculator_functions():
    """Test safe math functions."""
    tool = CalculatorTool()
    res = await tool.execute(expression="sqrt(144) + abs(-10)")
    assert res.success is True
    assert res.output["result"] == 22

    res_pi = await tool.execute(expression="round(pi, 2)")
    assert res_pi.success is True
    assert res_pi.output["result"] == 3.14


@pytest.mark.asyncio
async def test_calculator_division_by_zero():
    """Test division by zero protection."""
    tool = CalculatorTool()
    res = await tool.execute(expression="10 / 0")
    assert res.success is False
    assert "Division by zero" in res.error


@pytest.mark.asyncio
async def test_calculator_eval_injection_blocked():
    """Test that arbitrary code execution / imports are blocked."""
    tool = CalculatorTool()
    # Attempting to call non-math builtins
    res = await tool.execute(expression="__import__('os').system('ls')")
    assert res.success is False

    res2 = await tool.execute(expression="open('/etc/passwd')")
    assert res2.success is False
