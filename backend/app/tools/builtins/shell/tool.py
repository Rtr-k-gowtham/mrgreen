"""
MR.GREEN — Sandboxed Shell Tool

Provides restricted command execution within the sandbox environment.
Disabled by default; requires explicit approval for every run.
"""

from typing import Any

from app.sandbox.manager import sandbox_manager
from app.sandbox.security import is_command_safe
from app.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """Tool for sandboxed shell command execution."""

    def __init__(self, initially_enabled: bool = False) -> None:
        self._enabled = initially_enabled

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute restricted shell commands within the sandbox environment (Disabled by default)."

    @property
    def category(self) -> str:
        return "shell"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute inside sandbox",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Execution timeout in seconds (default 30, max 60)",
                },
            },
            "required": ["command"],
        }

    @property
    def permissions(self) -> list[str]:
        return ["shell.execute"]

    @property
    def risk_level(self) -> str:
        return "critical"

    @property
    def requires_approval(self) -> bool:
        return True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, val: bool) -> None:
        self._enabled = val

    async def execute(self, **kwargs: Any) -> ToolResult:
        if not self._enabled:
            return ToolResult(
                success=False,
                error="Shell tool is disabled by default. Enable it via API before execution.",
            )

        args = kwargs
        if "input" in kwargs and isinstance(kwargs["input"], dict):
            args = kwargs["input"]

        command = args.get("command")
        if not command:
            return ToolResult(success=False, error="Missing required argument 'command'")

        clean_cmd = str(command).strip()

        # Check safety filter
        is_safe, error_reason = is_command_safe(clean_cmd)
        if not is_safe:
            return ToolResult(
                success=False,
                error=f"Command rejected by security filter: {error_reason}",
                output={"command": clean_cmd},
            )

        timeout = min(int(args.get("timeout_seconds", 30)), 60)

        # Run via SandboxManager
        result = await sandbox_manager.execute_command(clean_cmd, timeout_seconds=timeout)

        return ToolResult(
            success=result.success,
            output={
                "command": clean_cmd,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            },
            error=result.error if not result.success else None,
            duration_ms=result.duration_ms,
        )
