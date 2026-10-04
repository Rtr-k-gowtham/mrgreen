"""
MR.GREEN — Tools Routes

GET /api/tools — List all registered tools
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_tool_registry
from app.tools.registry import ToolRegistry

router = APIRouter(prefix="/api")


class ToolResponse(BaseModel):
    """A registered tool."""
    name: str
    description: str
    input_schema: dict
    permissions: list[str]
    requires_approval: bool


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolResponse]:
    """List all registered tools available to the agent."""
    tools = registry.list_all()
    return [
        ToolResponse(
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            permissions=tool.permissions,
            requires_approval=tool.requires_approval,
        )
        for tool in tools
    ]
