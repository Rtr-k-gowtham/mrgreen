"""
MR.GREEN — File Reader Tool

Safely reads files contained strictly within the designated workspace.
Enforces path traversal protection and max file size limits.
"""

from typing import Any

from app.sandbox.security import is_path_safe
from app.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    """Tool for reading workspace files safely."""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read contents of a file inside the approved MR.GREEN workspace."

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to read relative to workspace (e.g. 'notes.txt', 'data/summary.json')",
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Optional maximum number of bytes to read (default 500000)",
                },
            },
            "required": ["path"],
        }

    @property
    def permissions(self) -> list[str]:
        return ["filesystem.read"]

    @property
    def risk_level(self) -> str:
        return "low"

    async def execute(self, **kwargs: Any) -> ToolResult:
        rel_path = kwargs.get("path")
        if not rel_path and "input" in kwargs and isinstance(kwargs["input"], dict):
            rel_path = kwargs["input"].get("path")

        if not rel_path:
            return ToolResult(
                success=False,
                error="Missing required argument 'path'",
            )

        max_bytes = kwargs.get("max_bytes", 500_000)

        # Security check: workspace containment & path traversal validation
        is_safe, resolved_path, error_reason = is_path_safe(rel_path)
        if not is_safe or resolved_path is None:
            return ToolResult(
                success=False,
                error=f"Security check failed: {error_reason}",
                output={"path": str(rel_path)},
            )

        if not resolved_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {rel_path}",
                output={"path": str(rel_path)},
            )

        if resolved_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Path is a directory, not a file: {rel_path}",
                output={"path": str(rel_path)},
            )

        try:
            file_size = resolved_path.stat().st_size
            with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(int(max_bytes))

            truncated = file_size > len(content.encode("utf-8"))

            return ToolResult(
                success=True,
                output={
                    "path": str(rel_path),
                    "content": content,
                    "size_bytes": file_size,
                    "lines": content.count("\n") + 1 if content else 0,
                    "truncated": truncated,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file: {str(e)}",
                output={"path": str(rel_path)},
            )
