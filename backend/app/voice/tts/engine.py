"""
MR.GREEN — Voice Engine Orchestrator

Manages active TTS providers (ElevenLabs, CosyVoice), voice profiles,
language detection, format reporting, and audio routing.
"""

import logging
from typing import Any, AsyncIterator

from app.config import get_settings
from app.voice.tts.base import BaseTTSProvider, detect_language
from app.voice.tts.cosyvoice import CosyVoiceProvider
from app.voice.tts.elevenlabs import ElevenLabsProvider

logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Central Voice Engine for MR.GREEN.

    Orchestrates ElevenLabs (primary cloud neural TTS) and CosyVoice (local neural TTS).
    Provides automatic format discovery (MP3/WAV) and seamless failover.
    """

    def __init__(self) -> None:
        settings = get_settings()

        # Register providers
        self.providers: dict[str, BaseTTSProvider] = {
            "elevenlabs": ElevenLabsProvider(),
            "cosyvoice": CosyVoiceProvider(),
        }

        # Select active provider and default voice profile
        if self.providers["elevenlabs"].is_available():
            self.active_provider_name = "elevenlabs"
            self.default_profile = getattr(settings, "elevenlabs_voice_id", "JBFqnCBsd6RMkjVDRZzb")
        else:
            self.active_provider_name = "cosyvoice"
            self.default_profile = settings.default_voice_profile

        logger.info(
            "[TTS_PROVIDER_SELECTED] Active TTS provider: %s (ElevenLabs configured: %s, CosyVoice ready: %s)",
            self.active_provider_name,
            self.providers["elevenlabs"].is_available(),
            self.providers["cosyvoice"].is_available(),
        )

    @property
    def active_provider(self) -> BaseTTSProvider:
        """Return the current active TTS provider."""
        return self.providers[self.active_provider_name]

    @property
    def audio_format(self) -> str:
        """Return the audio format of the active TTS provider ('mp3' or 'wav')."""
        return getattr(self.active_provider, "audio_format", "wav")

    def get_status(self) -> dict[str, Any]:
        """Return status for all registered voice providers."""
        profiles = list(self.providers["cosyvoice"].get_status().get("available_profiles", []))
        if self.providers["elevenlabs"].is_available():
            profiles.extend(self.providers["elevenlabs"].get_status().get("available_profiles", []))

        return {
            "active_provider": self.active_provider_name,
            "audio_format": self.audio_format,
            "default_profile": self.default_profile,
            "available_profiles": profiles,
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
        Synthesize text into audio chunks using the appropriate TTS provider.
        Automatically falls back to secondary provider if the primary provider fails.
        """
        profile_id = voice_profile_id or self.default_profile
        lang = language or detect_language(text)

        # Primary routing: ElevenLabs is the primary neural TTS provider when available
        if self.providers["elevenlabs"].is_available():
            provider = self.providers["elevenlabs"]
        elif profile_id and (
            profile_id.startswith("GREEN_")
            or profile_id in ("GREEN_DEFAULT", "GREEN_TAMIL", "GREEN_DEEP", "GREEN_CALM")
        ):
            provider = self.providers["cosyvoice"]
        else:
            provider = self.active_provider

        try:
            async for chunk in provider.synthesize(
                text=text,
                voice_profile_id=profile_id,
                language=lang,
            ):
                yield chunk
        except Exception as err:
            fallback_name = "cosyvoice" if provider == self.providers["elevenlabs"] else "elevenlabs"
            fallback_provider = self.providers.get(fallback_name)
            if fallback_provider and fallback_provider.is_available():
                logger.warning(
                    "[TTS_PROVIDER_FAILOVER] TTS provider '%s' failed (%s). Failing over to '%s'.",
                    getattr(provider, "name", "active_provider"),
                    err,
                    fallback_name,
                )
                async for chunk in fallback_provider.synthesize(
                    text=text,
                    voice_profile_id=profile_id,
                    language=lang,
                ):
                    yield chunk
            else:
                logger.error("TTS synthesis failed on %s: %s", getattr(provider, "name", "TTS"), err)
                raise


# Global voice engine singleton
global_voice_engine = VoiceEngine()
