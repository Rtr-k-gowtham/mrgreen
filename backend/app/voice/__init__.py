"""
MR.GREEN — Voice Package

Provides real-time conversational voice sessions, CosyVoice neural TTS,
STT abstractions, and WebSocket protocol handling.
"""

from app.voice.protocol import PROTOCOL_VERSION, ClientEventType, ServerEventType, VoiceState
from app.voice.session import VoiceSession
from app.voice.manager import VoiceSessionManager, voice_session_manager
from app.voice.websocket import router as voice_router

__all__ = [
    "PROTOCOL_VERSION",
    "ClientEventType",
    "ServerEventType",
    "VoiceState",
    "VoiceSession",
    "VoiceSessionManager",
    "voice_session_manager",
    "voice_router",
]
