"""
MR.GREEN — Voice Engine Orchestrator

Manages active TTS providers, voice profiles, language detection, and audio routing.
"""

import logging
from typing import Any, AsyncIterator

from app.config import get_settings
from app.voice.tts.base import BaseTTSProvider, VoiceProfile, detect_language
from app.voice.tts.cosyvoice import CosyVoiceProvider

logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Central Voice Engine for MR.GREEN.

    Manages provider selection, voice cloning profiles, and streaming speech synthesis.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.default_profile = settings.default_voice_profile

        # Register providers
        self.providers: dict[str, BaseTTSProvider] = {
            "cosyvoice": CosyVoiceProvider(),
        }
        self.active_provider_name = "cosyvoice"

    @property
    def active_provider(self) -> BaseTTSProvider:
        """Return the current active TTS provider."""
        return self.providers[self.active_provider_name]

    def get_status(self) -> dict[str, Any]:
        """Return status for all registered voice providers."""
        return {
            "active_provider": self.active_provider_name,
            "default_profile": self.default_profile,
            "providers": {
                name: provider.get_status()
                for name, provider in self.providers.items()
            },
        }

    async def synthesize_stream(
        self,
        text: str,
        voice_profile_id: str | None = None,
        language: str | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text into audio chunks using the active TTS provider.
        Automatically detects Tamil vs English if language is not provided.
        """
        profile_id = voice_profile_id or self.default_profile
        lang = language or detect_language(text)

        async for chunk in self.active_provider.synthesize(
            text=text,
            voice_profile_id=profile_id,
            language=lang,
        ):
            yield chunk


# Global voice engine singleton
global_voice_engine = VoiceEngine()
