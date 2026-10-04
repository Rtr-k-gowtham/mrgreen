"""
MR.GREEN — Browser STT Provider

Handles real-time speech recognition streamed from the client browser / mobile device.
Supports streaming interim results and final transcription dispatch.
"""

from typing import Any
from app.voice.stt.base import BaseSTTProvider


class BrowserSTTProvider(BaseSTTProvider):
    """
    Browser-assisted Speech-to-Text provider.
    Transcribes audio on the user device via Web Speech API and routes
    interim and final transcripts to the MR.GREEN Voice Session.
    """

    def __init__(self) -> None:
        self.name = "BrowserSTTProvider"

    def is_available(self) -> bool:
        return True

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": "client_assisted",
            "is_available": self.is_available(),
            "streaming_support": True,
        }

    async def transcribe_audio_chunk(
        self,
        audio_chunk: bytes,
        is_final: bool = False,
    ) -> str | None:
        # Browser STT transmits transcript text events directly
        return None
