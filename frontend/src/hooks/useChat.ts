import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessage, ToolActivity } from '../types/chat';
import { VoiceProfileId, VoiceState, SupportedLanguage } from '../types/voice';
import { api } from '../services/api';
import { VoiceSocketClient } from '../services/voiceSocket';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useSpeechSynthesis } from './useSpeechSynthesis';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [activeLanguage, setActiveLanguage] = useState<SupportedLanguage>('auto');
  const [activeVoiceProfile, setActiveVoiceProfile] = useState<VoiceProfileId>('GREEN_DEFAULT');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const tts = useSpeechSynthesis({
    defaultLanguage: activeLanguage === 'auto' ? 'en-IN' : activeLanguage,
    autoSpeak: true,
  });

  const sendMessageRef = useRef<(text: string) => Promise<void>>();
  const socketRef = useRef<VoiceSocketClient | null>(null);

  // Speech Recognition hook
  const stt = useSpeechRecognition({
    language: activeLanguage === 'auto' ? 'en-IN' : activeLanguage,
    onFinalResult: (finalText) => {
      if (finalText.trim() && sendMessageRef.current) {
        sendMessageRef.current(finalText.trim());
      }
    },
    onError: (err) => {
      setErrorMessage(err);
      setVoiceState('ERROR');
      setTimeout(() => {
        setVoiceState('IDLE');
      }, 3000);
    },
  });

  // Sync language with TTS and STT
  const handleLanguageChange = (lang: SupportedLanguage) => {
    setActiveLanguage(lang);
    if (lang !== 'auto') {
      tts.setLanguage(lang);
    }
  };

  // Immediate Barge-in / Interruption
  const interrupt = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.interrupt();
    }
    tts.stop();
    setVoiceState('INTERRUPTED');
    setTimeout(() => {
      setVoiceState('LISTENING');
    }, 100);
  }, [tts]);

  // Initialize VoiceSocketClient for real-time WebSocket connection
  useEffect(() => {
    const client = new VoiceSocketClient({
      onStateChange: (state) => {
        setVoiceState(state);
      },
      onPartialTranscript: (_text) => {
        // Can be displayed in input or HUD
      },
      onFinalTranscript: (text) => {
        if (text.trim() && sendMessageRef.current) {
          sendMessageRef.current(text.trim());
        }
      },
      onResponseDelta: (_delta) => {
        // Live streaming text updates
      },
      onResponseDone: (data) => {
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
      },
      onInterrupted: () => {
        setVoiceState('INTERRUPTED');
        setTimeout(() => setVoiceState('LISTENING'), 150);
      },
      onError: (err) => {
        setErrorMessage(err);
      },
    });

    socketRef.current = client;
    client.connect(conversationId || undefined, activeVoiceProfile, activeLanguage);

    return () => {
      client.disconnect();
    };
  }, [conversationId, activeVoiceProfile, activeLanguage]);

  // Health check polling
  const checkConnection = useCallback(async () => {
    try {
      const health = await api.checkHealth();
      const online = health.status === 'healthy' || health.status === 'ok';
      setIsOnline(online);
      if (!online) {
        setVoiceState('OFFLINE');
      }
      return online;
    } catch {
      setIsOnline(false);
      setVoiceState('OFFLINE');
      return false;
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 20000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  // Derive dynamic state from microphone / speech activities if socket is idle
  useEffect(() => {
    if (!isOnline) {
      setVoiceState('OFFLINE');
    } else if (errorMessage) {
      setVoiceState('ERROR');
    } else if (stt.isListening) {
      setVoiceState('LISTENING');
    } else if (tts.isSpeaking) {
      setVoiceState('ASSISTANT_SPEAKING');
    } else if (activeTool) {
      setVoiceState('TOOL_EXECUTING');
    } else if (isProcessing) {
      setVoiceState('THINKING');
    } else if (voiceState === 'CONNECTING' || voiceState === 'CONNECTED') {
      // keep current socket state
    } else {
      setVoiceState('IDLE');
    }
  }, [isOnline, errorMessage, stt.isListening, tts.isSpeaking, activeTool, isProcessing]);

  // Send message implementation
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Barge-in: Stop any current speech immediately
      interrupt();
      stt.stopListening();
      setErrorMessage(null);

      const userMsgId = `user-${Date.now()}`;
      const userMessage: ChatMessage = {
        id: userMsgId,
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'sent',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsProcessing(true);
      setVoiceState('THINKING');

      try {
        const response = await api.sendChatMessage({
          message: text.trim(),
          conversation_id: conversationId || undefined,
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
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status: 'sent',
          agentRunId: response.agent_run_id || undefined,
          toolActivities: toolActivities.length > 0 ? toolActivities : undefined,
          durationMs: response.duration_ms,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setIsProcessing(false);
        setActiveTool(null);
        setVoiceState('ASSISTANT_SPEAKING');

        // Play assistant speech
        if (tts.voiceEnabled) {
          tts.speak(response.response);
        }
      } catch (err: unknown) {
        setIsProcessing(false);
        setActiveTool(null);
        setVoiceState('ERROR');
        const errorText = err instanceof Error ? err.message : 'MR.GREEN encountered an error.';
        setErrorMessage(errorText);

        const errorMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: 'system',
          content: `⚠️ ${errorText}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status: 'error',
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    },
    [conversationId, tts, stt, interrupt]
  );

  sendMessageRef.current = sendMessage;

  const startNewChat = useCallback(() => {
    interrupt();
    stt.stopListening();
    setMessages([]);
    setConversationId(null);
    setErrorMessage(null);
    setActiveTool(null);
    setVoiceState('IDLE');
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
    [interrupt, stt]
  );

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
  };
}
