"""
MR.GREEN — Voice Session & State Machine

Manages a persistent, bidirectional WebSocket voice session between client and MR.GREEN.
Coordinates STT input, Agent loop execution, low-latency streaming TTS via CosyVoice,
and immediate barge-in / interruption handling.
"""

import asyncio
import base64
import logging
from typing import Any, Callable
from ulid import ULID
from fastapi import WebSocket

from app.agent.agent import Agent, AgentResponse
from app.ai.provider import AIProvider
from app.database.session import async_session_factory
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry
from app.voice.audio.buffer import SentenceBuffer
from app.voice.protocol import (
    PROTOCOL_VERSION,
    BaseVoiceEvent,
    ClientEventType,
    ServerEventType,
    VoiceState,
    current_iso_timestamp,
)
from app.voice.tts.engine import VoiceEngine, global_voice_engine

logger = logging.getLogger(__name__)


class VoiceSession:
    """
    Stateful real-time voice session coordinating speech input,
    agent execution, streaming TTS synthesis, and barge-in cancellation.
    """

    def __init__(
        self,
        session_id: str,
        websocket: WebSocket,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        voice_engine: VoiceEngine | None = None,
        conversation_id: str | None = None,
    ) -> None:
        self.session_id = session_id
        self.websocket = websocket
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.voice_engine = voice_engine or global_voice_engine
        self.conversation_id = conversation_id or str(ULID())

        self.state: VoiceState = VoiceState.CONNECTING
        self.active_voice_profile: str = "GREEN_DEFAULT"
        self.active_language: str = "auto"

        # Concurrency & interruption controls
        self._current_turn_task: asyncio.Task[Any] | None = None
        self._is_interrupted: bool = False
        self._is_closed: bool = False

    async def initialize(self) -> None:
        """Mark session connected and ready for speech interaction."""
        self.state = VoiceState.CONNECTED
        await self.send_event(
            ServerEventType.SESSION_READY,
            {
                "conversation_id": self.conversation_id,
                "supported_profiles": list(
                    self.voice_engine.active_provider.get_status().get("available_profiles", [])
                ),
            },
        )
        await self.transition_state(VoiceState.LISTENING)

    async def transition_state(self, new_state: VoiceState, extra: dict[str, Any] | None = None) -> None:
        """Update voice lifecycle state and notify client."""
        if self.state == new_state and not extra:
            return
        self.state = new_state
        payload = {"state": self.state.value}
        if extra:
            payload.update(extra)
        await self.send_event(ServerEventType.VOICE_STATE, payload)

    async def send_event(self, event_type: ServerEventType, payload: dict[str, Any] | None = None) -> None:
        """Transmit a structured protocol event to the client over WebSocket."""
        if self._is_closed:
            return
        event = BaseVoiceEvent(
            protocol_version=PROTOCOL_VERSION,
            session_id=self.session_id,
            type=event_type.value,
            timestamp=current_iso_timestamp(),
            payload=payload or {},
        )
        try:
            await self.websocket.send_json(event.to_json_dict())
        except Exception as e:
            logger.warning("Failed to send WebSocket event %s to session %s: %s", event_type, self.session_id, e)

    async def handle_user_interrupt(self) -> None:
        """
        Immediate Barge-in / Interruption.
        Cancels running speech synthesis, drops pending audio buffers,
        and immediately returns session to LISTENING.
        """
        logger.info("⚡ Barge-in interrupt triggered on session %s", self.session_id)
        self._is_interrupted = True

        if self._current_turn_task and not self._current_turn_task.done():
            self._current_turn_task.cancel()
            try:
                await self._current_turn_task
            except asyncio.CancelledError:
                pass

        await self.send_event(ServerEventType.ASSISTANT_INTERRUPTED)
        await self.transition_state(VoiceState.INTERRUPTED)
        # Brief pause to settle audio before returning to listening
        await asyncio.sleep(0.05)
        self._is_interrupted = False
        await self.transition_state(VoiceState.LISTENING)

    async def handle_transcript_input(self, text: str, is_final: bool = True) -> None:
        """
        Process speech transcript from STT provider or client.
        If interim, stream partial event; if final, trigger agent loop.
        """
        if not text or not text.strip():
            return

        clean_text = text.strip()

        if not is_final:
            await self.transition_state(VoiceState.USER_SPEAKING)
            await self.send_event(ServerEventType.TRANSCRIPT_PARTIAL, {"text": clean_text})
            return

        # User finished speaking: broadcast final transcript
        await self.send_event(ServerEventType.TRANSCRIPT_FINAL, {"text": clean_text})

        # Cancel any previous task if still running
        if self._current_turn_task and not self._current_turn_task.done():
            self._current_turn_task.cancel()

        # Launch agent reasoning turn
        self._current_turn_task = asyncio.create_task(self._execute_agent_turn(clean_text))

    async def _execute_agent_turn(self, user_message: str) -> None:
        """
        Executes the agent reasoning loop and streams CosyVoice TTS audio.
        """
        self._is_interrupted = False
        await self.transition_state(VoiceState.THINKING)
        await self.send_event(ServerEventType.AGENT_THINKING, {"message": user_message})

        try:
            # We open a scoped database session for the turn
            async with async_session_factory() as db:
                agent = Agent(
                    ai_provider=self.ai_provider,
                    tool_registry=self.tool_registry,
                    db_session=db,
                    memory_manager=self.memory_manager,
                )

                # Process through agent loop
                result: AgentResponse = await agent.process_message(
                    user_message=user_message,
                    conversation_id=self.conversation_id,
                )

                if self._is_interrupted:
                    logger.info("Agent turn cancelled after processing due to interruption.")
                    return

                response_text = result.content
                await self.send_event(
                    ServerEventType.RESPONSE_TEXT_DONE,
                    {
                        "response": response_text,
                        "conversation_id": self.conversation_id,
                        "agent_run_id": result.agent_run_id,
                        "iterations": result.iterations,
                    },
                )

                # Stream audio synthesis through CosyVoice
                await self._stream_tts(response_text)

                if not self._is_interrupted:
                    await self.transition_state(VoiceState.LISTENING)

        except asyncio.CancelledError:
            logger.info("Agent turn task cancelled.")
        except Exception as e:
            logger.error("Error executing agent voice turn: %s", str(e), exc_info=True)
            await self.send_event(ServerEventType.ERROR, {"error": "Voice assistant encountered an issue."})
            await self.transition_state(VoiceState.ERROR)
            await asyncio.sleep(1.0)
            await self.transition_state(VoiceState.LISTENING)

    async def _stream_tts(self, text: str) -> None:
        """
        Synthesize text into low-latency streaming audio chunks using CosyVoice.
        """
        if self._is_interrupted or not text.strip():
            return

        await self.transition_state(VoiceState.ASSISTANT_SPEAKING)
        sentence_buffer = SentenceBuffer()
        sentences = sentence_buffer.add_delta(text)
        sentences.extend(sentence_buffer.flush())

        if not sentences:
            sentences = [text]

        for sentence in sentences:
            if self._is_interrupted:
                break

            await self.send_event(ServerEventType.RESPONSE_TEXT_DELTA, {"delta": sentence})
            await self.send_event(ServerEventType.AUDIO_START, {"text": sentence})

            try:
                async for chunk in self.voice_engine.synthesize_stream(
                    text=sentence,
                    voice_profile_id=self.active_voice_profile,
                    language=None if self.active_language == "auto" else self.active_language,
                ):
                    if self._is_interrupted:
                        break
                    # Send audio chunk as base64 in structured event
                    b64_chunk = base64.b64encode(chunk).decode("ascii")
                    await self.send_event(
                        ServerEventType.AUDIO_CHUNK,
                        {"audio_data": b64_chunk, "format": "wav", "sample_rate": 22050},
                    )

                await self.send_event(ServerEventType.AUDIO_END)

            except Exception as e:
                logger.error("TTS stream error for sentence '%s': %s", sentence[:30], str(e))
                await self.send_event(ServerEventType.ERROR, {"error": "TTS audio streaming error."})

    async def close(self) -> None:
        """Gracefully terminate session."""
        self._is_closed = True
        if self._current_turn_task and not self._current_turn_task.done():
            self._current_turn_task.cancel()
        self.state = VoiceState.DISCONNECTED
