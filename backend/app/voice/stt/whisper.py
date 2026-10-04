"""
MR.GREEN — Local Whisper STT Provider

Architecture plug-point for on-device/local Whisper model transcription.
"""

from typing import Any
from app.voice.stt.base import BaseSTTProvider


class LocalWhisperProvider(BaseSTTProvider):
    """
    Local Whisper STT Provider.
    Ready for integration with whisper.cpp or faster-whisper on dedicated hardware.
    """

    def __init__(self, model_size: str = "base") -> None:
        self.name = "LocalWhisperProvider"
        self.model_size = model_size
        self._is_loaded = False

    def is_available(self) -> bool:
        return self._is_loaded

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": "local_neural",
            "model_size": self.model_size,
            "is_available": self.is_available(),
            "streaming_support": True,
        }

    async def transcribe_audio_chunk(
        self,
        audio_chunk: bytes,
        is_final: bool = False,
    ) -> str | None:
        return None
