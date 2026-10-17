"""
MR.GREEN — ElevenLabs TTS Provider

Implements low-latency neural speech synthesis via the ElevenLabs REST API.
Streams audio chunks incrementally directly from the /stream endpoint.
"""

import logging
from typing import Any, AsyncIterator
import httpx

from app.config import get_settings
from app.voice.tts.base import BaseTTSProvider

logger = logging.getLogger(__name__)

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


class ElevenLabsProvider(BaseTTSProvider):
    """
    ElevenLabs Text-to-Speech provider.

    Streams compressed MP3 audio chunks via the ElevenLabs streaming endpoint.
    Designed for real-time conversational pipelines with sub-second TTFA.
    """

    audio_format: str = "mp3"

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str | None = None,
        timeout: int | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else getattr(settings, "elevenlabs_api_key", "")
        self.voice_id = voice_id or getattr(settings, "elevenlabs_voice_id", "JBFqnCBsd6RMkjVDRZzb")
        self.model_id = model_id or getattr(settings, "elevenlabs_tts_model_id", "eleven_flash_v2_5")
        self.timeout = timeout or getattr(settings, "elevenlabs_timeout", 30)
        self._client: httpx.AsyncClient | None = None

    def is_available(self) -> bool:
        """Check if ElevenLabs API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def get_status(self) -> dict[str, Any]:
        """Return diagnostic health and config status."""
        return {
            "provider": "elevenlabs",
            "is_available": self.is_available(),
            "model_id": self.model_id,
            "voice_id": self.voice_id,
            "format": self.audio_format,
            "available_profiles": [self.voice_id],
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the pooled HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=ELEVENLABS_API_BASE,
                timeout=httpx.Timeout(self.timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=60.0),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def synthesize(
        self,
        text: str,
        voice_profile_id: str = "GREEN_DEFAULT",
        language: str | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text into low-latency MP3 audio chunks via ElevenLabs /stream API.
        """
        clean_text = text.strip()
        if not clean_text:
            return

        if not self.is_available():
            raise RuntimeError("ElevenLabs API key is not configured.")

        client = await self._get_client()

        # Map UI voice profiles to proven ElevenLabs voices
        profile_map = {
            "GREEN_DEFAULT": self.voice_id,
            "GREEN_DEEP": "pNInz6obpgDQGcFmaJgB",   # Adam (deep)
            "GREEN_CALM": "IKne3meq5aSn9XLyUdCD",   # Charlie (calm)
            "GREEN_TAMIL": self.voice_id,          # Multilingual Flash v2.5 fluent Tamil
        }

        # Resolve voice id: if voice_profile_id is in profile_map, use it;
        # if it looks like an explicit ElevenLabs ID (>10 chars), use it; else default.
        if voice_profile_id in profile_map:
            target_voice = profile_map[voice_profile_id]
        elif voice_profile_id and len(voice_profile_id) > 10:
            target_voice = voice_profile_id
        else:
            target_voice = self.voice_id

        endpoint = f"/text-to-speech/{target_voice}/stream"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload: dict[str, Any] = {
            "text": clean_text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    err_text = err_body.decode("utf-8", errors="ignore")
                    logger.error("ElevenLabs TTS error %d: %s", response.status_code, err_text)
                    response.raise_for_status()

                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception as e:
            logger.error("ElevenLabs streaming synthesis failed: %s", str(e))
            raise
