"""
MR.GREEN — STT Provider Base Interface

Defines the contract for Speech-to-Text transcription engines.
Supports streaming partial and final transcripts.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseSTTProvider(ABC):
    """Abstract interface for Speech-to-Text transcription."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether provider is operational."""
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Return provider configuration and capabilities."""
        pass

    @abstractmethod
    async def transcribe_audio_chunk(
        self,
        audio_chunk: bytes,
        is_final: bool = False,
    ) -> str | None:
        """Process incoming raw audio bytes and return transcribed text if ready."""
        pass
