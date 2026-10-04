"""
MR.GREEN — WebSocket Voice Route

Endpoint: WS /api/voice/ws
Maintains persistent, real-time bidirectional communication for audio streaming,
agent reasoning progress, CosyVoice audio output, and barge-in / interruption handling.
"""

import json
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_ai_provider, get_memory_manager, get_tool_registry
from app.ai.provider import AIProvider
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry
from app.voice.manager import voice_session_manager
from app.voice.protocol import ClientEventType, ServerEventType
from app.voice.session import VoiceSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice")


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    ai_provider: AIProvider = Depends(get_ai_provider),
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> None:
    """
    WebSocket endpoint for MR.GREEN real-time voice sessions.
    """
    await websocket.accept()

    session: VoiceSession = voice_session_manager.create_session(
        websocket=websocket,
        ai_provider=ai_provider,
        tool_registry=tool_registry,
        memory_manager=memory_manager,
    )

    await session.initialize()

    try:
        while True:
            # Receive text or JSON event from client
            raw_message = await websocket.receive_text()
            try:
                data = json.loads(raw_message)
            except Exception:
                logger.warning("Received invalid JSON payload on voice WS: %s", raw_message[:50])
                continue

            event_type = data.get("type")
            payload = data.get("payload") or {}
            # Flatten if fields sent at top level
            if not payload:
                payload = {k: v for k, v in data.items() if k not in ("protocol_version", "session_id", "type", "timestamp")}

            if event_type == ClientEventType.PING.value:
                await session.send_event(ServerEventType.PONG)

            elif event_type == ClientEventType.USER_INTERRUPT.value:
                # Immediate barge-in
                await session.handle_user_interrupt()

            elif event_type in (ClientEventType.TRANSCRIPT_INPUT.value, "transcript.input"):
                text = payload.get("text") or data.get("text", "")
                is_final = payload.get("is_final", True) if "is_final" in payload else data.get("is_final", True)
                await session.handle_transcript_input(text=text, is_final=is_final)

            elif event_type == ClientEventType.SESSION_START.value:
                if "voice_profile" in payload:
                    session.active_voice_profile = payload["voice_profile"]
                if "language" in payload:
                    session.active_language = payload["language"]
                if "conversation_id" in payload:
                    session.conversation_id = payload["conversation_id"]

            elif event_type == ClientEventType.AUDIO_START.value:
                # User began speaking (client VAD or mic press)
                if session.state.value == "ASSISTANT_SPEAKING":
                    await session.handle_user_interrupt()

            elif event_type == ClientEventType.SESSION_STOP.value:
                break

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected for session %s", session.session_id)
    except Exception as e:
        logger.error("Unexpected error in voice WebSocket loop: %s", str(e), exc_info=True)
    finally:
        await voice_session_manager.remove_session(session.session_id)


@router.get("/status")
async def voice_status() -> dict:
    """Return health and provider metrics for the voice subsystem."""
    from app.voice.tts.engine import global_voice_engine
    return {
        "status": "healthy",
        "engine": global_voice_engine.get_status(),
        "active_sessions": len(voice_session_manager.active_sessions),
    }
