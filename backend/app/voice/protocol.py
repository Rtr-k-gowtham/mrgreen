"""
MR.GREEN — Voice Protocol & Event Specifications

Version: 1
Defines structured events, voice session states, and message payload models
for bidirectional WebSocket communication between Client and MR.GREEN Voice Session.
"""

import enum
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

PROTOCOL_VERSION = "1"


class VoiceState(str, enum.Enum):
    """Explicit lifecycle states for MR.GREEN Voice Session."""
    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    LISTENING = "LISTENING"
    USER_SPEAKING = "USER_SPEAKING"
    PROCESSING = "PROCESSING"
    THINKING = "THINKING"
    TOOL_EXECUTING = "TOOL_EXECUTING"
    ASSISTANT_SPEAKING = "ASSISTANT_SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class ClientEventType(str, enum.Enum):
    """Events initiated by the client browser/mobile device."""
    SESSION_START = "session.start"
    AUDIO_START = "audio.start"
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_END = "audio.end"
    TRANSCRIPT_INPUT = "transcript.input"  # Client-side STT final/interim input
    USER_INTERRUPT = "user.interrupt"
    PING = "ping"
    SESSION_STOP = "session.stop"


class ServerEventType(str, enum.Enum):
    """Events transmitted from MR.GREEN Voice Session to client."""
    SESSION_READY = "session.ready"
    VOICE_STATE = "voice.state"
    TRANSCRIPT_PARTIAL = "transcript.partial"
    TRANSCRIPT_FINAL = "transcript.final"
    AGENT_THINKING = "agent.thinking"
    AGENT_TOOL_START = "agent.tool_start"
    AGENT_TOOL_END = "agent.tool_end"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_TEXT_DONE = "response.text.done"
    AUDIO_START = "audio.start"
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_END = "audio.end"
    ASSISTANT_INTERRUPTED = "assistant.interrupted"
    ERROR = "error"
    PONG = "pong"


def current_iso_timestamp() -> str:
    """Generate RFC3339 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class BaseVoiceEvent(BaseModel):
    """Base event model adhering to Section 22 specification."""
    protocol_version: str = PROTOCOL_VERSION
    session_id: str
    type: str
    timestamp: str = Field(default_factory=current_iso_timestamp)
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "session_id": self.session_id,
            "type": self.type,
            "timestamp": self.timestamp,
            **self.payload,
        }
