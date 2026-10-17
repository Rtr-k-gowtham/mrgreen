"""
Tests for Google Gemini AI Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.gemini import GeminiProvider
from app.ai.provider import AIMessage


@pytest.mark.asyncio
async def test_gemini_provider_message_formatting():
    """Test that AIMessage objects are formatted into Gemini contents and system_instruction."""
    provider = GeminiProvider(api_key="test-key", model="gemini-flash-latest")

    messages = [
        AIMessage(role="system", content="System instruction 1"),
        AIMessage(role="user", content="Hello"),
        AIMessage(role="assistant", content="Hi there!"),
        AIMessage(role="user", content="How are you?"),
    ]

    system_instruction, contents = provider._build_contents_and_system(
        messages=messages,
        system_prompt="Base system prompt",
    )

    assert system_instruction is not None
    assert "Base system prompt" in system_instruction["parts"][0]["text"]
    assert "System instruction 1" in system_instruction["parts"][0]["text"]

    assert len(contents) == 3
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "Hello"
    assert contents[1]["role"] == "model"
    assert contents[1]["parts"][0]["text"] == "Hi there!"
    assert contents[2]["role"] == "user"
    assert contents[2]["parts"][0]["text"] == "How are you?"

    await provider.close()


@pytest.mark.asyncio
async def test_gemini_provider_generate_mock():
    """Test GeminiProvider generate method with mocked response."""
    provider = GeminiProvider(api_key="test-key", model="gemini-flash-latest")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {"parts": [{"text": "Hello, I am MR.GREEN!"}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {"totalTokenCount": 25},
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.is_closed = False

    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.generate(
            messages=[AIMessage(role="user", content="Hi")],
        )

        assert resp.content == "Hello, I am MR.GREEN!"
        assert resp.provider == "gemini"
        assert resp.token_count == 25
        assert resp.finish_reason == "STOP"

    await provider.close()
