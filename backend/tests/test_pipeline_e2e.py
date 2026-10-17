"""
End-to-end integration test verifying Gemini streaming to ElevenLabs synthesis.
"""

import asyncio
import time
import pytest

from app.ai.gemini import GeminiProvider
from app.ai.provider import AIMessage
from app.voice.audio.buffer import SentenceBuffer
from app.voice.tts.engine import VoiceEngine


@pytest.mark.asyncio
async def test_full_conversational_pipeline_live():
    """Verify live Gemini stream feeding into ElevenLabs incremental audio generation."""
    gemini = GeminiProvider(model="gemini-flash-latest")
    voice_engine = VoiceEngine()
    sentence_buffer = SentenceBuffer()

    assert voice_engine.active_provider_name == "elevenlabs"

    user_prompt = "Say hello from MR.GREEN in one short sentence."
    t0 = time.monotonic()
    first_token_time = None
    first_audio_chunk_time = None

    ready_sentences = []
    total_audio_bytes = 0

    async for delta in gemini.generate_stream([AIMessage(role="user", content=user_prompt)]):
        if first_token_time is None:
            first_token_time = time.monotonic() - t0

        sents = sentence_buffer.add_delta(delta)
        for s in sents:
            ready_sentences.append(s)
            async for chunk in voice_engine.synthesize_stream(s):
                if first_audio_chunk_time is None:
                    first_audio_chunk_time = time.monotonic() - t0
                total_audio_bytes += len(chunk)

    for s in sentence_buffer.flush():
        ready_sentences.append(s)
        async for chunk in voice_engine.synthesize_stream(s):
            if first_audio_chunk_time is None:
                first_audio_chunk_time = time.monotonic() - t0
            total_audio_bytes += len(chunk)

    assert len(ready_sentences) > 0
    assert total_audio_bytes > 1000
    assert first_token_time is not None
    assert first_audio_chunk_time is not None
