"""
MR.GREEN — Tools Routes

Endpoints for discovering, inspecting, executing, enabling/disabling tools,
and auditing tool execution logs.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_tool_executor, get_tool_registry
from app.database.models import ToolCall
from app.tools.executor import ToolExecutionResponse, ToolExecutor
from app.tools.registry import ToolRegistry

router = APIRouter(prefix="/api")


class ToolResponse(BaseModel):
    """A registered tool."""
    name: str
    version: str = "1.0.0"
    description: str
    category: str = "general"
    input_schema: dict = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    requires_approval: bool = False
    enabled: bool = True


class ToolExecuteRequest(BaseModel):
    """Input payload for tool execution."""
    arguments: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str | None = None
    agent_run_id: str | None = None


class ToolCallResponse(BaseModel):
    """Audit log entry for tool execution."""
    id: str
    tool_name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    status: str
    success: bool | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    created_at: str | None = None


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolResponse]:
    """List all registered tools available to the agent."""
    tools = registry.list_all()
    return [
        ToolResponse(
            name=tool.name,
            version=tool.version,
            description=tool.description,
            category=tool.category,
            input_schema=tool.input_schema,
            permissions=tool.permissions,
            risk_level=tool.risk_level,
            requires_approval=tool.requires_approval,
            enabled=registry.is_enabled(tool.name),
        )
        for tool in tools
    ]


@router.get("/tools/{tool_name}", response_model=ToolResponse)
async def get_tool(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolResponse:
    """Get metadata for a specific registered tool."""
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return ToolResponse(
        name=tool.name,
        version=tool.version,
        description=tool.description,
        category=tool.category,
        input_schema=tool.input_schema,
        permissions=tool.permissions,
        risk_level=tool.risk_level,
        requires_approval=tool.requires_approval,
        enabled=registry.is_enabled(tool.name),
    )


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    payload: dict[str, Any] | None = None,
    executor: ToolExecutor = Depends(get_tool_executor),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Execute a registered tool directly with given arguments.
    """
    # Accept either {"arguments": {...}} or raw dictionary of parameters directly
    args = {}
    conversation_id = None
    agent_run_id = None

    if payload:
        if "arguments" in payload and isinstance(payload["arguments"], dict):
            args = payload["arguments"]
            conversation_id = payload.get("conversation_id")
            agent_run_id = payload.get("agent_run_id")
        else:
            args = payload

    response: ToolExecutionResponse = await executor.execute(
        tool_name=tool_name,
        arguments=args,
        db_session=db,
        conversation_id=conversation_id,
        agent_run_id=agent_run_id,
    )

    return response.to_dict()


@router.post("/tools/{tool_name}/enable")
async def enable_tool(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Enable a tool in the registry."""
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    success = registry.enable(tool_name)
    await registry.sync_to_db(db)
    return {"name": tool_name, "enabled": True, "success": success}


@router.post("/tools/{tool_name}/disable")
async def disable_tool(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Disable a tool in the registry."""
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    success = registry.disable(tool_name)
    await registry.sync_to_db(db)
    return {"name": tool_name, "enabled": False, "success": success}


@router.get("/tool-calls", response_model=list[ToolCallResponse])
async def list_tool_calls(
    limit: int = Query(default=50, ge=1, le=200),
    tool_name: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[ToolCallResponse]:
    """Retrieve audit history of tool executions."""
    query = select(ToolCall).order_by(ToolCall.created_at.desc()).limit(limit)
    if tool_name:
        query = query.where(ToolCall.tool_name == tool_name)

    result = await db.execute(query)
    calls = result.scalars().all()

    return [
        ToolCallResponse(
            id=call.id,
            tool_name=call.tool_name,
            input_data=call.input_data or {},
            output_data=call.output_data or {},
            status=call.status or "completed",
            success=call.success,
            error_message=call.error_message,
            duration_ms=call.duration_ms,
            created_at=call.created_at.isoformat() if call.created_at else None,
        )
        for call in calls
    ]
