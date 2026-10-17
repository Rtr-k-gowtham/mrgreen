"""
Tests for ElevenLabs TTS Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.voice.tts.elevenlabs import ElevenLabsProvider


def test_elevenlabs_provider_init_and_status():
    """Test ElevenLabsProvider initialization, status and availability flags."""
    provider = ElevenLabsProvider(
        api_key="test-api-key",
        voice_id="test-voice-id",
        model_id="eleven_flash_v2_5",
    )

    assert provider.is_available() is True
    assert provider.audio_format == "mp3"

    status = provider.get_status()
    assert status["provider"] == "elevenlabs"
    assert status["is_available"] is True
    assert status["model_id"] == "eleven_flash_v2_5"
    assert status["voice_id"] == "test-voice-id"
    assert status["format"] == "mp3"


def test_elevenlabs_provider_unavailable_when_no_key():
    """Test ElevenLabsProvider is marked unavailable when api_key is missing."""
    provider = ElevenLabsProvider(api_key="")
    assert provider.is_available() is False


@pytest.mark.asyncio
async def test_elevenlabs_provider_synthesize_mock():
    """Test ElevenLabsProvider streaming synthesize with mocked HTTP response."""
    provider = ElevenLabsProvider(
        api_key="test-key",
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_flash_v2_5",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200

    async def mock_aiter_bytes(chunk_size=4096):
        yield b"chunk1"
        yield b"chunk2"

    mock_response.aiter_bytes = mock_aiter_bytes

    class MockStreamContext:
        async def __aenter__(self):
            return mock_response

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client = MagicMock()
    mock_client.stream.return_value = MockStreamContext()
    mock_client.is_closed = False

    with patch.object(provider, "_get_client", AsyncMock(return_value=mock_client)):
        chunks = []
        async for chunk in provider.synthesize(text="Hello MR.GREEN"):
            chunks.append(chunk)

        assert chunks == [b"chunk1", b"chunk2"]

    await provider.close()
