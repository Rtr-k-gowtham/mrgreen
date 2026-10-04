"""
MR.GREEN — TTS Provider Base Interface & Voice Profiles

Defines the contract for all Text-to-Speech engines in MR.GREEN.
Supports streaming audio synthesis, voice profiles, and status introspection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
import re


@dataclass
class VoiceProfile:
    """Represents a voice reference or character persona for MR.GREEN."""
    id: str
    name: str
    description: str
    reference_audio: str | None = None
    reference_text: str | None = None
    language: str = "en"  # "en", "ta", or "multilingual"
    metadata: dict[str, Any] = field(default_factory=dict)


def detect_language(text: str) -> str:
    """
    Detect whether text contains Tamil script or is English/other.
    Tamil Unicode block: U+0B80 - U+0BFF
    """
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    return "en"


class BaseTTSProvider(ABC):
    """Abstract interface for all MR.GREEN Text-to-Speech providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the TTS provider is initialized and ready for synthesis."""
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Return diagnostic health and hardware status."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_profile_id: str = "GREEN_DEFAULT",
        language: str | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text into an audio byte stream (e.g. PCM / WAV / MP3 chunks).
        Yields raw audio chunks as they become available.
        """
        pass
