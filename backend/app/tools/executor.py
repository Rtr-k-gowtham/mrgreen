"""
MR.GREEN — Tool Executor

Orchestrates tool validation, permissions, human approval gating,
isolated execution with timeout enforcement, and database audit logging.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.database.models import Approval, ApprovalStatus, ToolCall
from app.tools.base import BaseTool, ToolResult
from app.tools.permissions import permission_engine
from app.tools.registry import ToolRegistry, tool_registry

logger = logging.getLogger(__name__)


class ToolExecutionResponse:
    """Standardized response returned by the ToolExecutor."""

    def __init__(
        self,
        success: bool,
        tool: str,
        result: Any = None,
        duration_ms: int = 0,
        error: str | None = None,
        status: str = "completed",
        approval_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.tool = tool
        self.result = result
        self.duration_ms = duration_ms
        self.error = error
        self.status = status
        self.approval_id = approval_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "status": self.status,
            "approval_id": self.approval_id,
            "metadata": self.metadata,
        }


class ToolExecutor:
    """
    Executes tools with safety checks, permissions, and database auditing.
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        default_timeout: int = 60,
    ) -> None:
        self.registry = registry or tool_registry
        self.default_timeout = default_timeout

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        db_session: AsyncSession | None = None,
        conversation_id: str | None = None,
        agent_run_id: str | None = None,
        agent_step_id: str | None = None,
        is_pre_approved: bool = False,
        timeout: int | None = None,
    ) -> ToolExecutionResponse:
        """
        Execute a tool by name with full permission verification and auditing.
        """
        start_time = time.monotonic()
        input_args = arguments or {}
        exec_timeout = timeout or self.default_timeout

        # 1. Validate tool exists
        tool = self.registry.get(tool_name)
        if tool is None:
            err = f"Tool not found: '{tool_name}'"
            logger.warning(err)
            return ToolExecutionResponse(
                success=False,
                tool=tool_name,
                error=err,
                status="failed",
                duration_ms=0,
            )

        # 2. Check whether tool is enabled
        if not self.registry.is_enabled(tool_name):
            err = f"Tool '{tool_name}' is currently disabled."
            logger.warning(err)
            return ToolExecutionResponse(
                success=False,
                tool=tool_name,
                error=err,
                status="failed",
                duration_ms=0,
            )

        # 3. Check permissions
        has_perm, perm_err = permission_engine.check_permissions(
            tool_name=tool.name,
            declared_permissions=tool.permissions,
        )
        if not has_perm:
            return ToolExecutionResponse(
                success=False,
                tool=tool_name,
                error=perm_err,
                status="failed",
                duration_ms=0,
            )

        # 4. Check approval requirement
        needs_approval = (
            tool.requires_approval
            or permission_engine.requires_approval(tool.permissions, tool.risk_level)
        )

        if needs_approval and not is_pre_approved:
            approval_id = str(ULID())
            logger.warning(
                "Execution of '%s' halted: requires human approval (id: %s)",
                tool_name, approval_id,
            )

            # Record pending approval and tool call in database if session available
            if db_session:
                approval_rec = Approval(
                    id=approval_id,
                    resource_type="tool_call",
                    resource_id=approval_id,
                    action=f"execute_{tool_name}",
                    status=ApprovalStatus.PENDING,
                    reason=f"Tool '{tool_name}' requires approval (risk: {tool.risk_level})",
                    created_at=datetime.now(timezone.utc),
                    metadata_={
                        "tool_name": tool_name,
                        "arguments": input_args,
                        "conversation_id": conversation_id,
                        "agent_run_id": agent_run_id,
                    },
                )
                db_session.add(approval_rec)

                pending_call = ToolCall(
                    id=approval_id,
                    agent_step_id=agent_step_id,
                    conversation_id=conversation_id,
                    agent_run_id=agent_run_id,
                    tool_name=tool_name,
                    input_data=input_args,
                    output_data={},
                    status="pending_approval",
                    success=None,
                    created_at=datetime.now(timezone.utc),
                )
                db_session.add(pending_call)
                try:
                    await db_session.commit()
                except Exception as e:
                    logger.error("Failed to record pending approval in DB: %s", str(e))

            return ToolExecutionResponse(
                success=False,
                tool=tool_name,
                status="pending_approval",
                approval_id=approval_id,
                error=f"Execution requires explicit human approval for tool '{tool_name}' (Risk: {tool.risk_level})",
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )

        # 5. Execute tool with timeout
        logger.info("Executing tool '%s' with args %s (timeout: %ds)", tool_name, list(input_args.keys()), exec_timeout)
        try:
            tool_result: ToolResult = await asyncio.wait_for(
                tool.execute(**input_args),
                timeout=float(exec_timeout),
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            resp = ToolExecutionResponse(
                success=tool_result.success,
                tool=tool_name,
                result=tool_result.output,
                error=tool_result.error,
                duration_ms=duration_ms,
                status="completed" if tool_result.success else "failed",
                metadata=tool_result.metadata,
            )

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error("Tool '%s' timed out after %ds", tool_name, exec_timeout)
            resp = ToolExecutionResponse(
                success=False,
                tool=tool_name,
                error=f"Tool execution timed out after {exec_timeout} seconds",
                duration_ms=duration_ms,
                status="timeout",
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error("Tool '%s' execution raised unexpected error: %s", tool_name, str(e))
            resp = ToolExecutionResponse(
                success=False,
                tool=tool_name,
                error=f"Tool error: {str(e)}",
                duration_ms=duration_ms,
                status="failed",
            )

        # 6. Record audit log in database
        if db_session:
            try:
                call_id = str(ULID())
                call_record = ToolCall(
                    id=call_id,
                    agent_step_id=agent_step_id,
                    conversation_id=conversation_id,
                    agent_run_id=agent_run_id,
                    tool_name=tool_name,
                    input_data=input_args,
                    output_data=resp.result if isinstance(resp.result, dict) else {"raw": str(resp.result)},
                    status=resp.status,
                    success=resp.success,
                    error_message=resp.error,
                    duration_ms=resp.duration_ms,
                    created_at=datetime.now(timezone.utc),
                )
                db_session.add(call_record)
                await db_session.commit()
            except Exception as e:
                logger.error("Failed to record ToolCall audit log: %s", str(e))

        return resp


# Global tool executor instance
global_tool_executor = ToolExecutor()
