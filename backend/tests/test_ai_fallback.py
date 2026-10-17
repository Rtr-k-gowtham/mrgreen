"""
Tests for FallbackAIProvider (Gemini primary with Ollama fallback).
"""

from unittest.mock import AsyncMock
import pytest

from app.ai.provider import AIMessage, AIResponse
from app.api.dependencies import FallbackAIProvider


@pytest.mark.asyncio
async def test_fallback_ai_provider_primary_success():
    """Test that primary provider is used when it succeeds."""
    mock_primary = AsyncMock()
    mock_fallback = AsyncMock()

    mock_primary.generate.return_value = AIResponse(
        content="Primary answer",
        model="gemini-flash-latest",
        provider="gemini",
    )

    provider = FallbackAIProvider(
        primary=mock_primary,
        fallback=mock_fallback,
        primary_name="gemini",
        fallback_name="ollama",
    )

    resp = await provider.generate([AIMessage(role="user", content="Hello")])
    assert resp.content == "Primary answer"
    assert resp.provider == "gemini"
    assert mock_primary.generate.called
    assert not mock_fallback.generate.called


@pytest.mark.asyncio
async def test_fallback_ai_provider_failover():
    """Test that fallback provider is called with reason logged when primary raises an exception."""
    mock_primary = AsyncMock()
    mock_fallback = AsyncMock()

    mock_primary.generate.side_effect = RuntimeError("Gemini connection error")
    mock_fallback.generate.return_value = AIResponse(
        content="Fallback answer",
        model="qwen2.5:3b",
        provider="ollama",
    )

    provider = FallbackAIProvider(
        primary=mock_primary,
        fallback=mock_fallback,
        primary_name="gemini",
        fallback_name="ollama",
    )

    resp = await provider.generate([AIMessage(role="user", content="Hello")])
    assert resp.content == "Fallback answer"
    assert resp.provider == "ollama"
    assert mock_primary.generate.called
    assert mock_fallback.generate.called
