"""
MR.GREEN — Daily Logs Routes

GET /api/daily-logs — List activity logs
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DailyLog
from app.database.session import get_db_session

router = APIRouter(prefix="/api")


class DailyLogResponse(BaseModel):
    """A single daily log entry."""
    id: str
    event_type: str
    description: str
    tool_name: str | None
    success: bool | None
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/daily-logs", response_model=list[DailyLogResponse])
async def list_daily_logs(
    target_date: date | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db_session),
) -> list[DailyLogResponse]:
    """List activity logs, optionally filtered by date and type."""
    query = (
        select(DailyLog)
        .order_by(DailyLog.created_at.desc())
        .limit(limit)
    )

    if target_date:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        query = query.where(DailyLog.created_at >= start).where(DailyLog.created_at <= end)

    if event_type:
        query = query.where(DailyLog.event_type == event_type)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        DailyLogResponse(
            id=log.id,
            event_type=log.event_type,
            description=log.description,
            tool_name=log.tool_name,
            success=log.success,
            duration_ms=log.duration_ms,
            created_at=log.created_at,
        )
        for log in logs
    ]
