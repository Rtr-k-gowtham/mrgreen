"""
MR.GREEN — API Dependencies

Shared FastAPI dependencies for route injection.
"""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama import OllamaProvider
from app.ai.provider import AIProvider
from app.config import Settings, get_settings
from app.database.session import get_db_session
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry, tool_registry


def get_ai_provider() -> AIProvider:
    """Get the configured AI provider."""
    return OllamaProvider()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return tool_registry


def get_tool_executor() -> Any:
    """Get the global tool executor."""
    from app.tools.executor import global_tool_executor
    return global_tool_executor


async def get_memory_manager(
    db: AsyncSession = Depends(get_db_session),
    ai_provider: AIProvider = Depends(get_ai_provider),
    settings: Settings = Depends(get_settings),
) -> MemoryManager:
    """Get a memory manager instance with all dependencies."""
    return MemoryManager(
        db_session=db,
        ai_provider=ai_provider,
        short_term_limit=settings.short_term_memory_limit,
        extraction_enabled=settings.memory_extraction_enabled,
    )
