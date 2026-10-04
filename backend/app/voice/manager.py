"""
MR.GREEN — Voice Session Manager

Tracks active WebSocket sessions, manages session lifecycles,
and cleans up disconnected clients.
"""

import logging
from typing import Any
from fastapi import WebSocket
from ulid import ULID

from app.ai.provider import AIProvider
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry
from app.voice.session import VoiceSession
from app.voice.tts.engine import VoiceEngine, global_voice_engine

logger = logging.getLogger(__name__)


class VoiceSessionManager:
    """Manages active real-time voice sessions."""

    def __init__(self) -> None:
        self.active_sessions: dict[str, VoiceSession] = {}

    def create_session(
        self,
        websocket: WebSocket,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        voice_engine: VoiceEngine | None = None,
        conversation_id: str | None = None,
    ) -> VoiceSession:
        """Create and register a new VoiceSession."""
        session_id = str(ULID())
        session = VoiceSession(
            session_id=session_id,
            websocket=websocket,
            ai_provider=ai_provider,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            voice_engine=voice_engine or global_voice_engine,
            conversation_id=conversation_id,
        )
        self.active_sessions[session_id] = session
        logger.info("Created new voice session: %s", session_id)
        return session

    def get_session(self, session_id: str) -> VoiceSession | None:
        """Retrieve an active voice session by ID."""
        return self.active_sessions.get(session_id)

    async def remove_session(self, session_id: str) -> None:
        """Close and deregister an active voice session."""
        session = self.active_sessions.pop(session_id, None)
        if session:
            await session.close()
            logger.info("Closed voice session: %s (remaining: %d)", session_id, len(self.active_sessions))


# Global voice session manager singleton
voice_session_manager = VoiceSessionManager()
