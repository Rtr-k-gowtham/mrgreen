"""
MR.GREEN — API Dependencies

Shared FastAPI dependencies for route injection.
Provides Gemini primary AI provider with transparent Ollama fallback.
"""

import logging
from typing import Any, AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini import GeminiProvider
from app.ai.ollama import OllamaProvider
from app.ai.provider import AIMessage, AIProvider, AIResponse, EmbeddingResponse
from app.config import Settings, get_settings
from app.database.session import get_db_session
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry, tool_registry

logger = logging.getLogger(__name__)

__all__ = [
    "FallbackAIProvider",
    "get_ai_provider",
    "get_db_session",
    "get_memory_manager",
    "get_tool_executor",
    "get_tool_registry",
]


class FallbackAIProvider(AIProvider):
    """
    Resilient AI Provider combining Gemini as primary with Ollama as fallback.
    Logs all provider routing and failovers with explicit reasons.
    """

    def __init__(
        self,
        primary: AIProvider,
        fallback: AIProvider,
        primary_name: str = "gemini",
        fallback_name: str = "ollama",
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name
        logger.info(
            "[AI_PROVIDER_INITIALIZED] Primary: '%s' | Fallback: '%s'",
            self.primary_name,
            self.fallback_name,
        )

    async def generate(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        try:
            return await self.primary.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            )
        except Exception as err:
            logger.warning(
                "[AI_PROVIDER_SWITCH] Primary provider '%s' failed (%s). Switching to fallback provider '%s'.",
                self.primary_name,
                err,
                self.fallback_name,
            )
            return await self.fallback.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            )

    async def generate_stream(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        try:
            async for delta in self.primary.generate_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            ):
                yield delta
        except Exception as err:
            logger.warning(
                "[AI_PROVIDER_STREAM_SWITCH] Primary provider '%s' stream failed (%s). Switching to fallback provider '%s'.",
                self.primary_name,
                err,
                self.fallback_name,
            )
            async for delta in self.fallback.generate_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            ):
                yield delta

    async def embed(self, text: str) -> EmbeddingResponse:
        try:
            return await self.primary.embed(text)
        except Exception as err:
            logger.warning(
                "[AI_PROVIDER_EMBED_SWITCH] Primary provider '%s' embed failed (%s). Switching to fallback provider '%s'.",
                self.primary_name,
                err,
                self.fallback_name,
            )
            return await self.fallback.embed(text)

    async def health_check(self) -> dict[str, Any]:
        primary_health = await self.primary.health_check()
        if primary_health.get("status") == "healthy":
            return primary_health

        fallback_health = await self.fallback.health_check()
        return {
            "status": "degraded" if fallback_health.get("status") == "healthy" else "unhealthy",
            "active_provider": self.primary_name,
            "primary": primary_health,
            "fallback": fallback_health,
        }

    async def list_models(self) -> list[str]:
        try:
            return await self.primary.list_models()
        except Exception:
            return await self.fallback.list_models()


def get_ai_provider() -> AIProvider:
    """Get the configured AI provider based on application settings."""
    settings = get_settings()
    provider_name = (settings.ai_provider or "gemini").lower()

    if provider_name == "gemini" or settings.gemini_api_key:
        primary = GeminiProvider()
        fallback = OllamaProvider()
        return FallbackAIProvider(
            primary=primary,
            fallback=fallback,
            primary_name="gemini",
            fallback_name="ollama",
        )

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
