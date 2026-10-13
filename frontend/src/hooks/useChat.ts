import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessage, ToolActivity } from '../types/chat';
import { VoiceProfileId, VoiceState, SupportedLanguage } from '../types/voice';
import { api } from '../services/api';
import { VoiceSocketClient, VoiceDiagnosticEvent } from '../services/voiceSocket';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useSpeechSynthesis } from './useSpeechSynthesis';

/** Maximum wait (ms) for a WebSocket voice response before timing out. */
const VOICE_PROCESSING_TIMEOUT_MS = 90_000;

/** Delay (ms) after response.text.done before falling back to browser TTS. */
const TTS_FALLBACK_DELAY_MS = 1_500;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [activeLanguage, setActiveLanguage] = useState<SupportedLanguage>('auto');
  const [activeVoiceProfile, setActiveVoiceProfile] =
    useState<VoiceProfileId>('GREEN_DEFAULT');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [diagnosticEvents, setDiagnosticEvents] = useState<VoiceDiagnosticEvent[]>([]);

  // ── Refs for stable access inside callbacks ─────────────────────

  const socketRef = useRef<VoiceSocketClient | null>(null);
  const sendMessageRef = useRef<(text: string) => Promise<void>>();
  const conversationIdRef = useRef<string | null>(null);
  const wsProcessingRef = useRef<boolean>(false);
  const wsProcessingTimeoutRef = useRef<any>(null);
  const ttsFallbackTimerRef = useRef<any>(null);
  const receivedCosyAudioRef = useRef<boolean>(false);

  const tts = useSpeechSynthesis({
    defaultLanguage: activeLanguage === 'auto' ? 'en-IN' : activeLanguage,
    autoSpeak: true,
  });
  const ttsRef = useRef(tts);
  ttsRef.current = tts;

  // Keep conversationId ref in sync
  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  // ── Diagnostic logging ──────────────────────────────────────────

  const addDiagnostic = useCallback((event: VoiceDiagnosticEvent) => {
    setDiagnosticEvents((prev) => [...prev.slice(-99), event]);
  }, []);

  // ── Barge-in / Interruption ─────────────────────────────────────

  const interrupt = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.interrupt();
    }
    ttsRef.current.stop();

    // Clear fallback timers
    if (ttsFallbackTimerRef.current) {
      clearTimeout(ttsFallbackTimerRef.current);
      ttsFallbackTimerRef.current = null;
    }

    setVoiceState('INTERRUPTED');
    setTimeout(() => setVoiceState('IDLE'), 100);
  }, []);

  // ── WebSocket lifecycle (created ONCE on mount) ─────────────────

  useEffect(() => {
    const client = new VoiceSocketClient({
      onStateChange: (state) => {
        // Track connection-related states only when WS drives the session
        const wsActiveStates: VoiceState[] = [
          'LISTENING',
          'USER_SPEAKING',
          'THINKING',
          'PROCESSING',
          'TOOL_EXECUTING',
          'ASSISTANT_SPEAKING',
          'INTERRUPTED',
        ];
        if (wsActiveStates.includes(state)) {
          setVoiceState(state);
        }
        // Clear processing flag when backend returns to LISTENING
        if (state === 'LISTENING' && wsProcessingRef.current) {
          wsProcessingRef.current = false;
          setIsProcessing(false);
          if (wsProcessingTimeoutRef.current) {
            clearTimeout(wsProcessingTimeoutRef.current);
            wsProcessingTimeoutRef.current = null;
          }
        }
      },

      onPartialTranscript: (_text) => {
        // Backend echoes partial transcripts — could show in a HUD
      },

      onFinalTranscript: (_text) => {
        // Backend echoes the final transcript we sent — user message
        // was already added to chat when we submitted it locally.
      },

      onResponseDelta: (_delta) => {
        // Live streaming text updates (future progressive display)
      },

      onResponseDone: (data) => {
        // ── Assistant response received via WebSocket ──
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }

        // Clear processing timeout
        if (wsProcessingTimeoutRef.current) {
          clearTimeout(wsProcessingTimeoutRef.current);
          wsProcessingTimeoutRef.current = null;
        }

        const assistantMessage: ChatMessage = {
          id: `asst-ws-${Date.now()}`,
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'sent',
          agentRunId: data.agent_run_id || undefined,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setIsProcessing(false);
        wsProcessingRef.current = false;

        // Reset audio tracking for this response
        receivedCosyAudioRef.current = false;

        // ── TTS Fallback Logic ──
        // If CosyVoice is not available, use browser TTS as fallback.
        // Even if CosyVoice is supposedly available, set a timer:
        // if no audio.start arrives within TTS_FALLBACK_DELAY_MS,
        // fall back to browser TTS.
        if (ttsRef.current.voiceEnabled && data.response.trim()) {
          if (!socketRef.current?.isTtsAvailable()) {
            // CosyVoice confirmed unavailable — use browser TTS immediately
            ttsRef.current.speak(data.response);
          } else {
            // CosyVoice claims available — wait briefly for audio.start
            ttsFallbackTimerRef.current = setTimeout(() => {
              if (!receivedCosyAudioRef.current && ttsRef.current.voiceEnabled) {
                ttsRef.current.speak(data.response);
              }
            }, TTS_FALLBACK_DELAY_MS);
          }
        }
      },

      onAudioStart: () => {
        receivedCosyAudioRef.current = true;
        // Cancel browser TTS fallback since CosyVoice audio is streaming
        if (ttsFallbackTimerRef.current) {
          clearTimeout(ttsFallbackTimerRef.current);
          ttsFallbackTimerRef.current = null;
        }
        ttsRef.current.stop(); // Stop any browser TTS that may have started
        setVoiceState('ASSISTANT_SPEAKING');
      },

      onAudioPlaybackStarted: () => {
        setVoiceState('ASSISTANT_SPEAKING');
      },

      onAudioPlaybackEnded: () => {
        // Playback queue drained — will transition to LISTENING via WS state
      },

      onInterrupted: () => {
        if (ttsFallbackTimerRef.current) {
          clearTimeout(ttsFallbackTimerRef.current);
          ttsFallbackTimerRef.current = null;
        }
        ttsRef.current.stop();
        setVoiceState('INTERRUPTED');
        setTimeout(() => setVoiceState('IDLE'), 150);
      },

      onError: (err) => {
        setErrorMessage(err);
        wsProcessingRef.current = false;
        setIsProcessing(false);
        if (wsProcessingTimeoutRef.current) {
          clearTimeout(wsProcessingTimeoutRef.current);
          wsProcessingTimeoutRef.current = null;
        }
      },

      onDiagnostic: (event) => {
        addDiagnostic(event);
      },
    });

    socketRef.current = client;
    client.connect(undefined, 'GREEN_DEFAULT', 'auto');

    return () => {
      client.disconnect();
      if (wsProcessingTimeoutRef.current) {
        clearTimeout(wsProcessingTimeoutRef.current);
      }
      if (ttsFallbackTimerRef.current) {
        clearTimeout(ttsFallbackTimerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // ← Created once on mount — stable WebSocket lifecycle

  // ── Sync session params to existing WebSocket (no reconnect) ────

  useEffect(() => {
    if (socketRef.current?.isConnected()) {
      socketRef.current.updateSession(
        conversationId,
        activeVoiceProfile,
        activeLanguage,
      );
    }
  }, [conversationId, activeVoiceProfile, activeLanguage]);

  // ── Voice STT → WebSocket routing ───────────────────────────────

  const handleVoiceFinalResult = useCallback((finalText: string) => {
    if (!finalText.trim()) return;
    const text = finalText.trim();

    // Route through WebSocket when connected
    if (socketRef.current?.isConnected()) {
      // Add user message to chat immediately
      const userMessage: ChatMessage = {
        id: `user-voice-${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        status: 'sent',
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsProcessing(true);
      setErrorMessage(null);
      wsProcessingRef.current = true;

      // Processing timeout safety net
      wsProcessingTimeoutRef.current = setTimeout(() => {
        if (wsProcessingRef.current) {
          wsProcessingRef.current = false;
          setIsProcessing(false);
          setErrorMessage(
            'Voice processing timed out. Please try again.',
          );
          setVoiceState('ERROR');
          setTimeout(() => setVoiceState('IDLE'), 3000);
        }
      }, VOICE_PROCESSING_TIMEOUT_MS);

      socketRef.current.sendTranscript(text, true);
    } else {
      // Fall back to HTTP path
      sendMessageRef.current?.(text);
    }
  }, []);

  // ── Speech Recognition hook ─────────────────────────────────────

  const stt = useSpeechRecognition({
    language: activeLanguage === 'auto' ? 'en-IN' : activeLanguage,
    onFinalResult: handleVoiceFinalResult,
    onError: (err) => {
      setErrorMessage(err);
      addDiagnostic({
        timestamp: Date.now(),
        stage: 'STT_EMPTY_RESULT',
        detail: err,
        level: 'error',
      });
      setVoiceState('ERROR');
      setTimeout(() => setVoiceState('IDLE'), 3000);
    },
  });

  // ── Language change ─────────────────────────────────────────────

  const handleLanguageChange = (lang: SupportedLanguage) => {
    setActiveLanguage(lang);
    if (lang !== 'auto') {
      tts.setLanguage(lang);
    }
  };

  // ── Health check polling ────────────────────────────────────────

  const checkConnection = useCallback(async () => {
    try {
      const health = await api.checkHealth();
      const online = health.status === 'healthy' || health.status === 'ok';
      setIsOnline(online);
      if (!online) setVoiceState('OFFLINE');
      return online;
    } catch {
      setIsOnline(false);
      setVoiceState('OFFLINE');
      return false;
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 20_000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  // ── Derive UI voice state from local signals (non-WS) ──────────

  useEffect(() => {
    // Don't override WebSocket-driven states during voice processing
    if (wsProcessingRef.current) return;

    if (!isOnline) {
      setVoiceState('OFFLINE');
    } else if (stt.isListening) {
      setVoiceState('LISTENING');
    } else if (tts.isSpeaking) {
      setVoiceState('ASSISTANT_SPEAKING');
    } else if (activeTool) {
      setVoiceState('TOOL_EXECUTING');
    } else if (isProcessing) {
      setVoiceState('THINKING');
    }
    // Intentionally not forcing IDLE — let the current state persist
    // until a new explicit state change occurs.
  }, [isOnline, stt.isListening, tts.isSpeaking, activeTool, isProcessing]);

  // ── Send message via HTTP (text input and WS-down fallback) ─────

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Stop any current speech — NOT an interrupt (don't send WS event)
      tts.stop();
      if (stt.isListening) {
        stt.stopListening();
      }
      setErrorMessage(null);

      const userMsgId = `user-${Date.now()}`;
      const userMessage: ChatMessage = {
        id: userMsgId,
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        status: 'sent',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsProcessing(true);
      setVoiceState('THINKING');

      try {
        const response = await api.sendChatMessage({
          message: text.trim(),
          conversation_id: conversationIdRef.current || undefined,
        });

        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }

        // Fetch tool activity if an agent run was executed
        let toolActivities: ToolActivity[] = [];
        if (response.agent_run_id) {
          try {
            const runDetail = await api.getAgentRun(response.agent_run_id);
            if (runDetail && runDetail.steps) {
              toolActivities = runDetail.steps
                .filter((s) => s.tool_name)
                .map((s) => ({
                  id: s.id,
                  toolName: s.tool_name || 'Tool',
                  actionType: s.action_type,
                  success: s.success ?? true,
                  durationMs: s.duration_ms ?? undefined,
                }));
            }
          } catch {
            // Non-critical, ignore
          }
        }

        const assistantMsgId = response.message_id || `asst-${Date.now()}`;
        const assistantMessage: ChatMessage = {
          id: assistantMsgId,
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'sent',
          agentRunId: response.agent_run_id || undefined,
          toolActivities: toolActivities.length > 0 ? toolActivities : undefined,
          durationMs: response.duration_ms,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setIsProcessing(false);
        setVoiceState('IDLE');

        // Play assistant speech via browser TTS (HTTP path)
        if (tts.voiceEnabled) {
          tts.speak(response.response);
        }
      } catch (err: unknown) {
        setIsProcessing(false);
        setActiveTool(null);
        setVoiceState('ERROR');
        const errorText =
          err instanceof Error
            ? err.message
            : 'MR.GREEN encountered an error.';
        setErrorMessage(errorText);

        const errorMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: 'system',
          content: `⚠️ ${errorText}`,
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'error',
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    },
    [tts, stt],
  );

  sendMessageRef.current = sendMessage;

  // ── New chat / load conversation ────────────────────────────────

  const startNewChat = useCallback(() => {
    interrupt();
    stt.stopListening();
    setMessages([]);
    setConversationId(null);
    setErrorMessage(null);
    setActiveTool(null);
    setVoiceState('IDLE');
    wsProcessingRef.current = false;
  }, [interrupt, stt]);

  const loadConversation = useCallback(
    async (id: string) => {
      interrupt();
      stt.stopListening();
      setErrorMessage(null);
      setIsProcessing(true);

      try {
        const detail = await api.getConversation(id);
        if (detail) {
          setConversationId(detail.id);
          const mappedMessages: ChatMessage[] = detail.messages.map((m) => ({
            id: m.id,
            role: m.role as any,
            content: m.content,
            timestamp: new Date(m.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
            status: 'sent',
          }));
          setMessages(mappedMessages);
        }
      } catch {
        setErrorMessage('Failed to load conversation history.');
      } finally {
        setIsProcessing(false);
      }
    },
    [interrupt, stt],
  );

  // ── Return public API ───────────────────────────────────────────

  return {
    messages,
    conversationId,
    isOnline,
    isProcessing,
    activeTool,
    voiceState,
    orbState: voiceState, // backwards compatibility
    errorMessage,
    activeLanguage,
    activeVoiceProfile,
    setActiveVoiceProfile,
    setActiveLanguage: handleLanguageChange,
    stt,
    tts,
    interrupt,
    sendMessage,
    startNewChat,
    loadConversation,
    checkConnection,
    diagnosticEvents,
  };
}
