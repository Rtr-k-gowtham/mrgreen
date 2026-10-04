"""
MR.GREEN — Voice System & CosyVoice Tests

Tests voice engine, CosyVoice provider, multilingual synthesis (English & Tamil),
protocol serialization, sentence streaming buffer, and barge-in / state transitions.
"""

import pytest
from app.voice.audio.buffer import SentenceBuffer
from app.voice.protocol import (
    PROTOCOL_VERSION,
    BaseVoiceEvent,
    ClientEventType,
    ServerEventType,
    VoiceState,
)
from app.voice.tts.base import detect_language
from app.voice.tts.cosyvoice import CosyVoiceProvider
from app.voice.tts.engine import VoiceEngine


def test_language_detection() -> None:
    """Verify language detection for English, Tamil, and mixed dialogues."""
    assert detect_language("Hello, what is the weather today?") == "en"
    assert detect_language("வணக்கம். நான் MR.GREEN.") == "ta"
    assert detect_language("Green, இன்று website status என்ன?") == "ta"


def test_sentence_buffer_streaming() -> None:
    """Verify sentence buffering splits on punctuation boundaries."""
    buffer = SentenceBuffer(min_chunk_chars=5, max_chunk_chars=100)

    # Incomplete sentence
    s1 = buffer.add_delta("Hello there")
    assert len(s1) == 0

    # Add punctuation
    s2 = buffer.add_delta("! How are you today? ")
    assert len(s2) >= 1
    assert "Hello there!" in s2[0]

    # Flush tail
    buffer.add_delta("I am testing the voice engine")
    tail = buffer.flush()
    assert len(tail) == 1
    assert tail[0] == "I am testing the voice engine"


def test_voice_protocol_events() -> None:
    """Verify protocol event schema and versioning."""
    event = BaseVoiceEvent(
        session_id="test_session_123",
        type=ServerEventType.VOICE_STATE.value,
        payload={"state": VoiceState.LISTENING.value},
    )
    d = event.to_json_dict()
    assert d["protocol_version"] == PROTOCOL_VERSION
    assert d["session_id"] == "test_session_123"
    assert d["type"] == "voice.state"
    assert d["state"] == "LISTENING"


def test_cosyvoice_provider_status_and_profiles() -> None:
    """Verify CosyVoice provider initialization and registered voice profiles."""
    provider = CosyVoiceProvider()
    status = provider.get_status()

    assert status["name"] == "CosyVoiceProvider"
    assert "hardware" in status
    assert "GREEN_DEFAULT" in status["available_profiles"]
    assert "GREEN_DEEP" in status["available_profiles"]
    assert "GREEN_CALM" in status["available_profiles"]
    assert "GREEN_TAMIL" in status["available_profiles"]


@pytest.mark.asyncio
async def test_cosyvoice_english_synthesis() -> None:
    """Internal test: 'Hello, I am MR.GREEN.' generates valid speech audio chunks."""
    engine = VoiceEngine()
    text = "Hello, I am MR.GREEN."

    chunks = []
    async for chunk in engine.synthesize_stream(text, voice_profile_id="GREEN_DEFAULT"):
        chunks.append(chunk)

    total_bytes = sum(len(c) for c in chunks)
    assert len(chunks) > 0
    assert total_bytes > 44  # Exceeds standard 44-byte WAV header
    # Check RIFF header magic bytes
    full_audio = b"".join(chunks)
    assert full_audio.startswith(b"RIFF")


@pytest.mark.asyncio
async def test_cosyvoice_tamil_synthesis() -> None:
    """Internal test: 'வணக்கம். நான் MR.GREEN.' generates valid Tamil speech audio chunks."""
    engine = VoiceEngine()
    text = "வணக்கம். நான் MR.GREEN."

    chunks = []
    async for chunk in engine.synthesize_stream(text, voice_profile_id="GREEN_TAMIL"):
        chunks.append(chunk)

    total_bytes = sum(len(c) for c in chunks)
    assert len(chunks) > 0
    assert total_bytes > 44
    full_audio = b"".join(chunks)
    assert full_audio.startswith(b"RIFF")
