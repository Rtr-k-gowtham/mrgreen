import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessage, ToolActivity } from '../types/chat';
import { OrbState, SupportedLanguage } from '../types/voice';
import { api } from '../services/api';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useSpeechSynthesis } from './useSpeechSynthesis';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [orbState, setOrbState] = useState<OrbState>('IDLE');
  const [activeLanguage, setActiveLanguage] = useState<SupportedLanguage>('en-IN');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const tts = useSpeechSynthesis({
    defaultLanguage: activeLanguage,
    autoSpeak: true,
  });

  const sendMessageRef = useRef<(text: string) => Promise<void>>();

  // Speech Recognition hook
  const stt = useSpeechRecognition({
    language: activeLanguage,
    onFinalResult: (finalText) => {
      if (finalText.trim() && sendMessageRef.current) {
        sendMessageRef.current(finalText.trim());
      }
    },
    onError: (err) => {
      setErrorMessage(err);
      setOrbState('ERROR');
      setTimeout(() => {
        setOrbState('IDLE');
      }, 3000);
    },
  });

  // Sync language with TTS and STT
  const handleLanguageChange = (lang: SupportedLanguage) => {
    setActiveLanguage(lang);
    tts.setLanguage(lang);
  };

  // Health check polling
  const checkConnection = useCallback(async () => {
    try {
      const health = await api.checkHealth();
      const online = health.status === 'healthy' || health.status === 'ok';
      setIsOnline(online);
      if (!online) {
        setOrbState('OFFLINE');
      }
      return online;
    } catch {
      setIsOnline(false);
      setOrbState('OFFLINE');
      return false;
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 20000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  // Update Orb State dynamically based on system activities
  useEffect(() => {
    if (!isOnline) {
      setOrbState('OFFLINE');
    } else if (errorMessage) {
      setOrbState('ERROR');
    } else if (stt.isListening) {
      setOrbState('LISTENING');
    } else if (tts.isSpeaking) {
      setOrbState('SPEAKING');
    } else if (activeTool) {
      setOrbState('TOOL_EXECUTION');
    } else if (isProcessing) {
      setOrbState('THINKING');
    } else {
      setOrbState('IDLE');
    }
  }, [isOnline, errorMessage, stt.isListening, tts.isSpeaking, activeTool, isProcessing]);

  // Send message implementation
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Stop any current speech
      tts.stop();
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

      try {
        const response = await api.sendChatMessage({
          message: text.trim(),
          conversation_id: conversationId || undefined,
        });

        // Update active conversation ID
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

        // Speak the assistant's response via TTS
        if (tts.voiceEnabled) {
          tts.speak(response.response);
        }
      } catch (err: unknown) {
        setIsProcessing(false);
        setActiveTool(null);
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
    [conversationId, tts, stt]
  );

  sendMessageRef.current = sendMessage;

  const startNewChat = useCallback(() => {
    tts.stop();
    stt.stopListening();
    setMessages([]);
    setConversationId(null);
    setErrorMessage(null);
    setActiveTool(null);
    setOrbState('IDLE');
  }, [tts, stt]);

  const loadConversation = useCallback(
    async (id: string) => {
      tts.stop();
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
      } catch (err) {
        setErrorMessage('Failed to load conversation history.');
      } finally {
        setIsProcessing(false);
      }
    },
    [tts, stt]
  );

  return {
    messages,
    conversationId,
    isOnline,
    isProcessing,
    activeTool,
    orbState,
    errorMessage,
    activeLanguage,
    setActiveLanguage: handleLanguageChange,
    stt,
    tts,
    sendMessage,
    startNewChat,
    loadConversation,
    checkConnection,
  };
}
