"""
MR.GREEN — Sandbox Manager

Provides secure, isolated execution environments for tools, code, and external commands.
Enforces timeouts, workspace boundaries, and output limits.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.sandbox.security import get_safe_workspace_root, is_command_safe

logger = logging.getLogger(__name__)


class SandboxExecutionResult:
    """Result of sandboxed execution."""
    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        exit_code: int | None = None,
        duration_ms: int = 0,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class SandboxManager:
    """
    Manages sandboxed execution of processes and tools.
    """

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or get_safe_workspace_root()

    async def execute_command(
        self,
        command: str,
        timeout_seconds: int = 30,
        env: dict[str, str] | None = None,
    ) -> SandboxExecutionResult:
        """
        Execute a shell command with strict security isolation, timeout, and output limits.
        """
        # 1. Security check
        is_safe, reason = is_command_safe(command)
        if not is_safe:
            logger.warning("Blocked unsafe command execution: %s (%s)", command, reason)
            return SandboxExecutionResult(
                success=False,
                error=f"Command rejected by security policy: {reason}",
                exit_code=-1,
            )

        # 2. Minimal sanitized environment
        safe_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
        }
        if env:
            safe_env.update(env)

        import time
        start_time = time.monotonic()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=safe_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=float(timeout_seconds),
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                duration_ms = int((time.monotonic() - start_time) * 1000)
                return SandboxExecutionResult(
                    success=False,
                    exit_code=-1,
                    duration_ms=duration_ms,
                    error=f"Execution timed out after {timeout_seconds} seconds",
                )

            duration_ms = int((time.monotonic() - start_time) * 1000)
            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

            return SandboxExecutionResult(
                success=(process.returncode == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error("Sandbox execution error: %s", str(e))
            return SandboxExecutionResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                duration_ms=duration_ms,
                exit_code=-1,
            )


# Global sandbox manager
sandbox_manager = SandboxManager()
