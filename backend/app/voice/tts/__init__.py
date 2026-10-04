"""
MR.GREEN — TTS Package
"""

from app.voice.tts.base import BaseTTSProvider, VoiceProfile, detect_language
from app.voice.tts.cosyvoice import CosyVoiceProvider
from app.voice.tts.engine import VoiceEngine, global_voice_engine

__all__ = [
    "BaseTTSProvider",
    "VoiceProfile",
    "detect_language",
    "CosyVoiceProvider",
    "VoiceEngine",
    "global_voice_engine",
]
