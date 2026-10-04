"""
MR.GREEN — Agent Run Tracking Routes

Endpoints for tracking agent execution lifecycles, plans, and steps.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db_session
from app.database.models import AgentRun, AgentStep

router = APIRouter(prefix="/api/agent")


class StepResponse(BaseModel):
    id: str
    step_number: int
    action_type: str
    tool_name: str | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    success: bool | None = None
    duration_ms: int | None = None
    created_at: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    conversation_id: str
    status: str
    goal: str | None = None
    current_step: int = 0
    total_steps: int = 0
    iterations: int = 0
    max_iterations: int = 10
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class AgentRunDetailResponse(AgentRunResponse):
    steps: list[StepResponse] = Field(default_factory=list)


@router.get("/runs", response_model=list[AgentRunResponse])
async def list_agent_runs(
    limit: int = Query(default=30, ge=1, le=100),
    conversation_id: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[AgentRunResponse]:
    """List agent execution runs."""
    query = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
    if conversation_id:
        query = query.where(AgentRun.conversation_id == conversation_id)

    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        AgentRunResponse(
            id=run.id,
            conversation_id=run.conversation_id,
            status=run.status.value if hasattr(run.status, "value") else str(run.status),
            goal=run.goal,
            current_step=run.current_step or 0,
            total_steps=run.total_steps or 0,
            iterations=run.iterations or 0,
            max_iterations=run.max_iterations,
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            error_message=run.error_message,
        )
        for run in runs
    ]


@router.get("/runs/{run_id}", response_model=AgentRunDetailResponse)
async def get_agent_run(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> AgentRunDetailResponse:
    """Get details of a specific agent run including all execution steps."""
    result = await db.execute(
        select(AgentRun)
        .options(selectinload(AgentRun.steps))
        .where(AgentRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Agent run '{run_id}' not found")

    steps = [
        StepResponse(
            id=s.id,
            step_number=s.step_number,
            action_type=s.action_type,
            tool_name=s.tool_name,
            input_data=s.input_data or {},
            output_data=s.output_data or {},
            success=s.success,
            duration_ms=s.duration_ms,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in run.steps
    ]

    return AgentRunDetailResponse(
        id=run.id,
        conversation_id=run.conversation_id,
        status=run.status.value if hasattr(run.status, "value") else str(run.status),
        goal=run.goal,
        current_step=run.current_step or 0,
        total_steps=run.total_steps or 0,
        iterations=run.iterations or 0,
        max_iterations=run.max_iterations,
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        error_message=run.error_message,
        steps=steps,
    )
