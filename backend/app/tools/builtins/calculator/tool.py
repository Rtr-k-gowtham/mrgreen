"""
MR.GREEN — Safe Calculator Tool

Evaluates mathematical expressions safely using Python's ast module.
Never invokes eval() or exec().
"""

import ast
import math
import operator
from typing import Any

from app.tools.base import BaseTool, ToolResult

# Supported binary operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Supported unary operators
SAFE_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Safe mathematical functions & constants
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pow": pow,
    "min": min,
    "max": max,
    "ceil": math.ceil,
    "floor": math.floor,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_node(node: ast.AST) -> float | int:
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.Name):
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unknown or unauthorized identifier: '{node.id}'")

    if isinstance(node, ast.UnaryOp):
        op_func = SAFE_UNARY_OPERATORS.get(type(node.op))
        if not op_func:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.operand))

    if isinstance(node, ast.BinOp):
        op_func = SAFE_OPERATORS.get(type(node.op))
        if not op_func:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

        left = _eval_node(node.left)
        right = _eval_node(node.right)

        # Safety check for power overflow
        if isinstance(node.op, ast.Pow):
            if right > 1000 or (isinstance(left, (int, float)) and abs(left) > 100 and right > 50):
                raise ValueError("Exponent too large — calculation would overflow")

        try:
            return op_func(left, right)
        except ZeroDivisionError:
            raise ValueError("Division by zero")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct mathematical function calls are supported")

        func_name = node.func.id
        func = SAFE_FUNCTIONS.get(func_name)
        if not func:
            raise ValueError(f"Unknown or unauthorized function '{func_name}'")

        args = [_eval_node(arg) for arg in node.args]
        return func(*args)

    raise ValueError(f"Unsupported expression syntax: {type(node).__name__}")


def evaluate_expression(expr: str) -> float | int:
    """Parse and safely evaluate a mathematical expression."""
    clean_expr = expr.strip()
    if not clean_expr:
        raise ValueError("Expression cannot be empty")
    if len(clean_expr) > 200:
        raise ValueError("Expression exceeds maximum allowed length of 200 characters")

    try:
        parsed = ast.parse(clean_expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid mathematical syntax: {str(e)}")

    return _eval_node(parsed.body)


class CalculatorTool(BaseTool):
    """Tool for safely evaluating mathematical expressions without eval()."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform safe mathematical calculations using an AST-based evaluator."

    @property
    def category(self) -> str:
        return "math"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g. '25 * 4', 'sqrt(144) + 10')",
                }
            },
            "required": ["expression"],
        }

    @property
    def permissions(self) -> list[str]:
        return []

    @property
    def risk_level(self) -> str:
        return "low"

    async def execute(self, **kwargs: Any) -> ToolResult:
        expression = kwargs.get("expression")
        if not expression and "input" in kwargs and isinstance(kwargs["input"], dict):
            expression = kwargs["input"].get("expression")

        if not expression:
            return ToolResult(
                success=False,
                error="Missing required argument 'expression'",
            )

        try:
            val = evaluate_expression(str(expression))
            # Format nicely
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            return ToolResult(
                success=True,
                output={"expression": expression, "result": val},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                output={"expression": expression},
            )
