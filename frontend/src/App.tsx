import React, { useState } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/layout/Header';
import { MrGreenAssistantVisual } from './components/voice/MrGreenAssistantVisual';
import { BottomVoiceControl } from './components/voice/BottomVoiceControl';
import { VoiceSettingsModal } from './components/voice/VoiceSettingsModal';
import { VoiceDiagnosticPanel } from './components/voice/VoiceDiagnosticPanel';

export const App: React.FC = () => {
  const {
    messages,
    isOnline,
    isProcessing,
    voiceState,
    errorMessage,
    activeLanguage,
    activeVoiceProfile,
    setActiveVoiceProfile,
    setActiveLanguage,
    stt,
    tts,
    interrupt,
    sendMessage,
    startNewChat,
    diagnosticEvents,
    streamingResponse,
  } = useChat();

  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Extract latest assistant reply for subtle visual caption
  const lastAssistantMessage = messages
    .filter((m) => m.role === 'assistant')
    .slice(-1)[0]?.content;

  // Toggle voice input with immediate interruption of assistant speech
  const handleToggleListening = () => {
    if (stt.isListening || voiceState === 'LISTENING' || voiceState === 'USER_SPEAKING') {
      stt.stopListening();
    } else {
      // If assistant is currently speaking, barge-in / interrupt immediately
      if (tts.isSpeaking || voiceState === 'ASSISTANT_SPEAKING') {
        interrupt();
      }
      stt.startListening();
    }
  };

  const isActuallySpeaking = tts.isSpeaking || voiceState === 'ASSISTANT_SPEAKING' || voiceState === 'SPEAKING';
  const isActuallyListening = stt.isListening || voiceState === 'LISTENING' || voiceState === 'USER_SPEAKING';
  const isActuallyThinking = isProcessing || voiceState === 'THINKING' || voiceState === 'PROCESSING';

  return (
    <div className="flex flex-col h-screen max-h-screen bg-white text-slate-900 overflow-hidden font-sans select-none">
      {/* Header — Minimal Green MG Logo + Leaf & Settings */}
      <Header
        isOnline={isOnline}
        onNewChat={startNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Full-Screen Jarvis Experience */}
      <main className="flex-1 flex flex-col justify-between items-center max-w-2xl w-full mx-auto relative px-4 overflow-hidden">
        {/* Subtle Non-intrusive Error Toast (if any) */}
        {errorMessage && (
          <div className="w-full max-w-sm mt-3 animate-fade-in z-20">
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs px-3.5 py-2 rounded-2xl flex items-center justify-between shadow-sm">
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Center: Beautiful Futuristic MR.GREEN Assistant Visual & Status */}
        <div className="flex-1 flex items-center justify-center w-full">
          <MrGreenAssistantVisual
            voiceState={voiceState}
            isListening={isActuallyListening}
            isSpeaking={isActuallySpeaking}
            isProcessing={isActuallyThinking}
            isOnline={isOnline}
            interimTranscript={stt.interimTranscript}
            lastResponse={lastAssistantMessage}
            streamingResponse={streamingResponse}
            onRetry={startNewChat}
          />
        </div>

        {/* Bottom: Circular Microphone Control with Waveforms & Discreet Text Fallback */}
        <footer className="w-full flex-shrink-0">
          <BottomVoiceControl
            isListening={isActuallyListening}
            isSpeaking={isActuallySpeaking}
            isProcessing={isActuallyThinking}
            speechSupported={stt.isSupported}
            onToggleListen={handleToggleListening}
            onStopSpeaking={interrupt}
            onSendMessage={sendMessage}
            disabled={!isOnline}
          />
        </footer>
      </main>

      {/* Settings Modal */}
      <VoiceSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        voiceEnabled={tts.voiceEnabled}
        onToggleVoice={() => tts.setVoiceEnabled(!tts.voiceEnabled)}
        rate={tts.rate}
        onChangeRate={tts.setRate}
        language={activeLanguage}
        onChangeLanguage={setActiveLanguage}
        voiceProfile={activeVoiceProfile}
        onChangeVoiceProfile={setActiveVoiceProfile}
        onTestVoice={(text) => tts.speak(text)}
        voices={tts.voices}
        selectedVoice={tts.selectedVoice}
        onSelectVoice={tts.setSelectedVoice}
      />

      {/* Development-only Voice Diagnostic Panel */}
      <VoiceDiagnosticPanel
        voiceState={voiceState}
        isListening={stt.isListening}
        isSpeaking={tts.isSpeaking}
        isProcessing={isProcessing}
        isOnline={isOnline}
        sttError={stt.error}
        diagnosticEvents={diagnosticEvents}
      />
    </div>
  );
};
export default App;
