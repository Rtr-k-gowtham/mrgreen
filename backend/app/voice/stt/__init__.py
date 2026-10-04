"""
MR.GREEN — STT Package
"""

from app.voice.stt.base import BaseSTTProvider
from app.voice.stt.browser import BrowserSTTProvider
from app.voice.stt.whisper import LocalWhisperProvider

__all__ = [
    "BaseSTTProvider",
    "BrowserSTTProvider",
    "LocalWhisperProvider",
]
