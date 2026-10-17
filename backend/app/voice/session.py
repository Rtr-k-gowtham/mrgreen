"""
MR.GREEN — Voice Session & State Machine

Manages a persistent, bidirectional WebSocket voice session between client and MR.GREEN.
Coordinates STT input, Agent loop execution, low-latency streaming TTS via CosyVoice,
and immediate barge-in / interruption handling.
"""

import asyncio
import time
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
        self.active_voice_profile: str = self.voice_engine.default_profile
        self.active_language: str = "auto"

        # Concurrency & interruption controls
        self._current_turn_task: asyncio.Task[Any] | None = None
        self._current_tts_task: asyncio.Task[Any] | None = None
        self._is_interrupted: bool = False
        self._is_closed: bool = False

    async def initialize(self) -> None:
        """Mark session connected and ready for speech interaction."""
        self.state = VoiceState.CONNECTED
        tts_available = self.voice_engine.active_provider.is_available()
        logger.info(
            "[SESSION_READY] session=%s conversation=%s tts_available=%s",
            self.session_id, self.conversation_id, tts_available,
        )
        await self.send_event(
            ServerEventType.SESSION_READY,
            {
                "conversation_id": self.conversation_id,
                "tts_available": tts_available,
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

        if self._current_tts_task and not self._current_tts_task.done():
            self._current_tts_task.cancel()
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
            logger.info("[STT_EMPTY_RESULT] session=%s", self.session_id)
            return

        clean_text = text.strip()
        logger.info(
            "[USER_MESSAGE_RECEIVED] session=%s is_final=%s text_len=%d",
            self.session_id, is_final, len(clean_text),
        )

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
        turn_start = time.monotonic()
        logger.info(
            "[AGENT_STARTED] session=%s message='%s'",
            self.session_id, user_message[:80],
        )
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

                logger.info("[MODEL_INFERENCE_STARTED] session=%s conversation=%s", self.session_id, self.conversation_id)
                sentence_buffer = SentenceBuffer()
                accumulated_text: list[str] = []
                first_token_time: float | None = None
                first_audio_time: float | None = None
                tts_start = time.monotonic()

                # Pipelined TTS sentence queue & background consumer
                sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()

                async def _tts_consumer() -> None:
                    nonlocal first_audio_time
                    while True:
                        sent = await sentence_queue.get()
                        if sent is None:
                            sentence_queue.task_done()
                            break
                        if self._is_interrupted:
                            sentence_queue.task_done()
                            break
                        try:
                            if self.state != VoiceState.ASSISTANT_SPEAKING:
                                await self.transition_state(VoiceState.ASSISTANT_SPEAKING)
                            if first_audio_time is None:
                                first_audio_time = time.monotonic()
                                logger.info(
                                    "[FIRST_TTS_CHUNK] session=%s elapsed=%.2fs",
                                    self.session_id, first_audio_time - turn_start,
                                )
                            await self._stream_sentence_tts(sent)
                        except Exception as tts_err:
                            logger.error("TTS worker sentence error: %s", tts_err)
                        finally:
                            sentence_queue.task_done()

                self._current_tts_task = asyncio.create_task(_tts_consumer())

                # Stream response tokens directly from LLM without blocking on TTS
                try:
                    async for delta in agent.generate_response_stream(
                        user_message=user_message,
                        conversation_id=self.conversation_id,
                    ):
                        if self._is_interrupted:
                            break
                        if first_token_time is None:
                            first_token_time = time.monotonic()
                            logger.info(
                                "[FIRST_TOKEN_RECEIVED] session=%s elapsed=%.2fs",
                                self.session_id, first_token_time - turn_start,
                            )
                        accumulated_text.append(delta)
                        await self.send_event(ServerEventType.RESPONSE_TEXT_DELTA, {"delta": delta})

                        # As soon as sentence boundary is reached, queue for concurrent TTS synthesis
                        ready_sentences = sentence_buffer.add_delta(delta)
                        for sent in ready_sentences:
                            if not self._is_interrupted:
                                await sentence_queue.put(sent)

                    # Flush any remaining text in sentence buffer
                    tail_sentences = sentence_buffer.flush()
                    for sent in tail_sentences:
                        if not self._is_interrupted:
                            await sentence_queue.put(sent)

                    # Signal TTS consumer to complete and await audio completion
                    await sentence_queue.put(None)
                    if self._current_tts_task:
                        await self._current_tts_task

                except Exception as stream_err:
                    logger.warning("Streaming turn encountered error (%s), using batch fallback", stream_err)
                    if self._current_tts_task and not self._current_tts_task.done():
                        self._current_tts_task.cancel()

                full_response = "".join(accumulated_text).strip()
                if not full_response:
                    # Fallback to standard process_message if stream produced no text
                    logger.info("[STREAM_FALLBACK] Executing batch process_message")
                    result: AgentResponse = await agent.process_message(
                        user_message=user_message,
                        conversation_id=self.conversation_id,
                    )
                    full_response = result.content
                    await self._stream_tts(full_response)

                total_tts_time = time.monotonic() - tts_start
                logger.info("[TTS_STREAM_COMPLETED] session=%s tts_duration=%.2fs", self.session_id, total_tts_time)

                if self._is_interrupted:
                    logger.info("[VOICE_INTERRUPTED] Agent turn cancelled after processing.")
                    return

                await self.send_event(
                    ServerEventType.RESPONSE_TEXT_DONE,
                    {
                        "response": full_response,
                        "conversation_id": self.conversation_id,
                    },
                )

                # Record messages into memory & history
                self.memory_manager.short_term.add("user", user_message)
                self.memory_manager.short_term.add("assistant", full_response)

                turn_total = time.monotonic() - turn_start
                logger.info("[TURN_COMPLETED] session=%s total_time=%.2fs", self.session_id, turn_total)

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

    async def _stream_sentence_tts(self, sentence: str) -> None:
        """Stream audio chunks for a single sentence."""
        if self._is_interrupted or not sentence.strip():
            return
        audio_fmt = self.voice_engine.audio_format
        sample_rate = 44100 if audio_fmt == "mp3" else 22050
        await self.send_event(ServerEventType.AUDIO_START, {"text": sentence, "format": audio_fmt})
        try:
            async for chunk in self.voice_engine.synthesize_stream(
                text=sentence,
                voice_profile_id=self.active_voice_profile,
                language=None if self.active_language == "auto" else self.active_language,
            ):
                if self._is_interrupted:
                    break
                b64_chunk = base64.b64encode(chunk).decode("ascii")
                await self.send_event(
                    ServerEventType.AUDIO_CHUNK,
                    {"audio_data": b64_chunk, "format": audio_fmt, "sample_rate": sample_rate},
                )
            await self.send_event(ServerEventType.AUDIO_END, {"format": audio_fmt})
        except Exception as e:
            logger.error("TTS stream error for sentence '%s': %s", sentence[:30], str(e))
            await self.send_event(ServerEventType.ERROR, {"error": "TTS audio streaming error."})

    async def _stream_tts(self, text: str) -> None:
        """
        Synthesize text into low-latency streaming audio chunks using CosyVoice.
        """
        if self._is_interrupted or not text.strip():
            return

        tts_start = time.monotonic()
        await self.transition_state(VoiceState.ASSISTANT_SPEAKING)
        sentence_buffer = SentenceBuffer()
        sentences = sentence_buffer.add_delta(text)
        sentences.extend(sentence_buffer.flush())

        if not sentences:
            sentences = [text]

        logger.info("[TTS_STARTED] session=%s sentences=%d text_len=%d", self.session_id, len(sentences), len(text))

        for sentence in sentences:
            if self._is_interrupted:
                break
            await self.send_event(ServerEventType.RESPONSE_TEXT_DELTA, {"delta": sentence})
            await self._stream_sentence_tts(sentence)

        logger.info("[TTS_COMPLETED] session=%s elapsed=%.2fs", self.session_id, time.monotonic() - tts_start)

    async def close(self) -> None:
        """Gracefully terminate session."""
        self._is_closed = True
        if self._current_tts_task and not self._current_tts_task.done():
            self._current_tts_task.cancel()
        if self._current_turn_task and not self._current_turn_task.done():
            self._current_turn_task.cancel()
        self.state = VoiceState.DISCONNECTED
