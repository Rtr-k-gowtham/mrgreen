"""
MR.GREEN — File Writer Tool

Safely creates or appends text to files strictly inside the approved workspace.
Enforces path traversal protection and max write size limits.
"""

from typing import Any

from app.sandbox.security import is_path_safe
from app.tools.base import BaseTool, ToolResult

MAX_WRITE_BYTES = 1_000_000  # 1MB limit per write operation


class FileWriteTool(BaseTool):
    """Tool for writing files safely inside workspace."""

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write or append text content to a file inside the approved MR.GREEN workspace."

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
                    "description": "Relative file path inside workspace (e.g. 'output/report.txt')",
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write to the file",
                },
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "Write mode: 'write' (overwrite) or 'append'. Defaults to 'write'.",
                },
            },
            "required": ["path", "content"],
        }

    @property
    def permissions(self) -> list[str]:
        return ["filesystem.write"]

    @property
    def risk_level(self) -> str:
        return "medium"

    async def execute(self, **kwargs: Any) -> ToolResult:
        args = kwargs
        if "input" in kwargs and isinstance(kwargs["input"], dict):
            args = kwargs["input"]

        rel_path = args.get("path")
        content = args.get("content")
        mode = args.get("mode", "write")

        if not rel_path:
            return ToolResult(success=False, error="Missing required argument 'path'")
        if content is None:
            return ToolResult(success=False, error="Missing required argument 'content'")

        str_content = str(content)
        content_bytes = len(str_content.encode("utf-8"))
        if content_bytes > MAX_WRITE_BYTES:
            return ToolResult(
                success=False,
                error=f"Content exceeds maximum write size of {MAX_WRITE_BYTES} bytes ({content_bytes} bytes provided)",
            )

        # Security check: workspace containment & path traversal
        is_safe, resolved_path, error_reason = is_path_safe(rel_path)
        if not is_safe or resolved_path is None:
            return ToolResult(
                success=False,
                error=f"Security check failed: {error_reason}",
                output={"path": str(rel_path)},
            )

        try:
            # Create parent directories inside workspace if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            file_mode = "a" if mode.lower() == "append" else "w"
            with open(resolved_path, file_mode, encoding="utf-8") as f:
                f.write(str_content)

            total_size = resolved_path.stat().st_size
            return ToolResult(
                success=True,
                output={
                    "path": str(rel_path),
                    "bytes_written": content_bytes,
                    "total_size_bytes": total_size,
                    "mode": mode,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {str(e)}",
                output={"path": str(rel_path)},
            )
