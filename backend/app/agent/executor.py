"""
MR.GREEN — Agent Executor

Executes planned actions — either tool calls via ToolExecutor or AI generation.
Acts as the bridge between the planner's decisions and actual execution.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import AIMessage, AIProvider, AIResponse
from app.tools.base import ToolResult
from app.tools.executor import ToolExecutionResponse, ToolExecutor
from app.tools.registry import ToolRegistry, tool_registry

logger = logging.getLogger(__name__)


class Executor:
    """
    Executes actions determined by the planner.

    Handles:
    - Direct AI generation
    - Tool execution with full safety, permission, approval, and audit checks
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        registry: ToolRegistry | None = None,
        tool_timeout: int = 60,
    ) -> None:
        self.ai_provider = ai_provider
        self.tool_registry = registry or tool_registry
        self.tool_timeout = tool_timeout
        self.tool_executor = ToolExecutor(registry=self.tool_registry, default_timeout=tool_timeout)

    async def generate_response(
        self,
        messages: list[AIMessage],
        system_prompt: str,
        temperature: float = 0.7,
    ) -> AIResponse:
        """Generate a direct AI response."""
        return await self.ai_provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        db_session: AsyncSession | None = None,
        conversation_id: str | None = None,
        agent_run_id: str | None = None,
        agent_step_id: str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute a tool by name with the given arguments via ToolExecutor.
        """
        combined_args = dict(arguments or {})
        combined_args.update(kwargs)

        exec_resp: ToolExecutionResponse = await self.tool_executor.execute(
            tool_name=tool_name,
            arguments=combined_args,
            db_session=db_session,
            conversation_id=conversation_id,
            agent_run_id=agent_run_id,
            agent_step_id=agent_step_id,
        )

        return ToolResult(
            success=exec_resp.success,
            output=exec_resp.result,
            error=exec_resp.error,
            duration_ms=exec_resp.duration_ms,
            metadata=exec_resp.metadata,
        )
