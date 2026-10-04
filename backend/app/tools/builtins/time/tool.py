"""
MR.GREEN — Current Time Tool

Returns current UTC and localized time information.
"""

from datetime import datetime, timezone
from typing import Any
import zoneinfo

from app.tools.base import BaseTool, ToolResult


class TimeTool(BaseTool):
    """Tool for retrieving current date, time, and timezone information."""

    @property
    def name(self) -> str:
        return "time"

    @property
    def description(self) -> str:
        return "Return current server and UTC date and time information."

    @property
    def category(self) -> str:
        return "system"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Optional timezone name (e.g. 'UTC', 'local', 'America/New_York', 'Asia/Kolkata'). Defaults to 'UTC'.",
                }
            },
        }

    @property
    def permissions(self) -> list[str]:
        return []

    @property
    def risk_level(self) -> str:
        return "low"

    async def execute(self, **kwargs: Any) -> ToolResult:
        tz_name = kwargs.get("timezone", "UTC")
        if not tz_name and "input" in kwargs and isinstance(kwargs["input"], dict):
            tz_name = kwargs["input"].get("timezone", "UTC")
        if not tz_name:
            tz_name = "UTC"

        now_utc = datetime.now(timezone.utc)

        try:
            if tz_name.lower() in ("local", "server"):
                target_dt = datetime.now().astimezone()
                tz_label = str(target_dt.tzinfo)
            else:
                tz = zoneinfo.ZoneInfo(tz_name)
                target_dt = now_utc.astimezone(tz)
                tz_label = tz_name
        except Exception:
            # Fallback to UTC if requested timezone is unrecognized
            target_dt = now_utc
            tz_label = f"UTC (fallback, '{tz_name}' invalid)"

        return ToolResult(
            success=True,
            output={
                "iso": target_dt.isoformat(),
                "formatted": target_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "date": target_dt.strftime("%Y-%m-%d"),
                "time": target_dt.strftime("%H:%M:%S"),
                "weekday": target_dt.strftime("%A"),
                "timezone": tz_label,
                "timestamp": int(target_dt.timestamp()),
            },
        )
