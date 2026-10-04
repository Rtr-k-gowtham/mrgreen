"""
MR.GREEN — Daily Activity Logs

Records every important agent activity for auditing and review.
Every tool call, conversation, memory operation, and error is logged.
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.database.models import DailyLog

logger = logging.getLogger(__name__)


class DailyLogger:
    """
    Records structured activity logs to PostgreSQL.

    These logs serve as an audit trail and can be reviewed
    through the API or used for behavioral analysis.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log(
        self,
        event_type: str,
        description: str,
        session_id: str | None = None,
        tool_name: str | None = None,
        success: bool | None = None,
        duration_ms: int | None = None,
        metadata: dict | None = None,
    ) -> DailyLog:
        """Record an activity log entry."""
        entry = DailyLog(
            id=str(ULID()),
            session_id=session_id,
            event_type=event_type,
            description=description,
            tool_name=tool_name,
            success=success,
            duration_ms=duration_ms,
            metadata_=metadata or {},
        )
        self.db.add(entry)
        logger.debug(
            "Daily log: [%s] %s (tool=%s, success=%s)",
            event_type, description, tool_name, success,
        )
        return entry

    async def log_chat(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        duration_ms: int | None = None,
    ) -> DailyLog:
        """Log a chat interaction."""
        return await self.log(
            event_type="chat",
            description=f"User: {user_message[:100]}...",
            session_id=session_id,
            success=True,
            duration_ms=duration_ms,
            metadata={
                "user_message_length": len(user_message),
                "response_length": len(assistant_response),
            },
        )

    async def log_memory_stored(
        self,
        key: str,
        memory_type: str,
        session_id: str | None = None,
    ) -> DailyLog:
        """Log a memory storage event."""
        return await self.log(
            event_type="memory_stored",
            description=f"Stored memory: {key} (type={memory_type})",
            session_id=session_id,
            success=True,
        )

    async def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: int | None = None,
        error: str | None = None,
        session_id: str | None = None,
    ) -> DailyLog:
        """Log a tool execution."""
        return await self.log(
            event_type="tool_call",
            description=f"Tool call: {tool_name}",
            tool_name=tool_name,
            session_id=session_id,
            success=success,
            duration_ms=duration_ms,
            metadata={"error": error} if error else None,
        )

    async def log_error(
        self,
        description: str,
        error: str,
        session_id: str | None = None,
    ) -> DailyLog:
        """Log an error event."""
        return await self.log(
            event_type="error",
            description=description,
            session_id=session_id,
            success=False,
            metadata={"error": error},
        )

    async def get_logs_for_date(
        self,
        target_date: date | None = None,
        limit: int = 100,
    ) -> list[DailyLog]:
        """Get all logs for a specific date (default: today)."""
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end = datetime.combine(target_date, datetime.max.time(), tzinfo=timezone.utc)

        result = await self.db.execute(
            select(DailyLog)
            .where(DailyLog.created_at >= start)
            .where(DailyLog.created_at <= end)
            .order_by(DailyLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_logs(self, limit: int = 50) -> list[DailyLog]:
        """Get the most recent log entries."""
        result = await self.db.execute(
            select(DailyLog)
            .order_by(DailyLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
