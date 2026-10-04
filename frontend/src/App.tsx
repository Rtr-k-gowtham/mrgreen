import React, { useState } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/layout/Header';
import { HistoryDrawer } from './components/layout/HistoryDrawer';
import { ChatList } from './components/chat/ChatList';
import { ChatInput } from './components/chat/ChatInput';
import { VoiceSettingsModal } from './components/voice/VoiceSettingsModal';

export const App: React.FC = () => {
  const {
    messages,
    conversationId,
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
    loadConversation,
  } = useChat();

  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Toggle voice input with immediate interruption of assistant speech
  const handleToggleListening = () => {
    if (stt.isListening) {
      stt.stopListening();
    } else {
      // If assistant is currently speaking, barge in / interrupt immediately
      if (tts.isSpeaking || voiceState === 'ASSISTANT_SPEAKING') {
        interrupt();
      }
      stt.startListening();
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-[#050806] text-zinc-100 overflow-hidden font-sans select-none">
      {/* Top Header — Cybernetic Minimal HUD */}
      <Header
        isOnline={isOnline}
        onNewChat={startNewChat}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Container — The Conversation is the Hero (NO ORB) */}
      <main className="flex-1 flex flex-col min-h-0 max-w-4xl w-full mx-auto relative overflow-hidden">
        {/* Global Error Banner (if any) */}
        {errorMessage && (
          <div className="px-4 py-1.5 flex-shrink-0 animate-fade-in">
            <div className="bg-rose-950/80 border border-rose-800 text-rose-200 text-xs px-3 py-1.5 rounded-xl flex items-center justify-between font-mono">
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Conversation Message List — Occupies Full Viewport */}
        <section
          aria-label="Conversation messages"
          className="flex-1 min-h-0 flex flex-col overflow-hidden relative"
        >
          <ChatList
            messages={messages}
            isProcessing={isProcessing || voiceState === 'THINKING'}
            onSelectPrompt={sendMessage}
            onSpeak={(text) => tts.speak(text)}
          />
        </section>

        {/* Bottom Composer with Voice Controls & Real-Time Barge-in */}
        <footer className="flex-shrink-0">
          <ChatInput
            onSendMessage={sendMessage}
            isListening={stt.isListening || voiceState === 'LISTENING' || voiceState === 'USER_SPEAKING'}
            isSpeaking={tts.isSpeaking || voiceState === 'ASSISTANT_SPEAKING'}
            isProcessing={isProcessing || voiceState === 'THINKING'}
            interimTranscript={stt.interimTranscript}
            voiceState={voiceState}
            speechSupported={stt.isSupported}
            onToggleListen={handleToggleListening}
            onStopSpeaking={interrupt}
            voiceEnabled={tts.voiceEnabled}
            onToggleVoice={() => tts.setVoiceEnabled(!tts.voiceEnabled)}
            activeLanguage={activeLanguage}
            onChangeLanguage={setActiveLanguage}
            disabled={!isOnline}
          />
        </footer>
      </main>

      {/* Slide-out History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        activeConversationId={conversationId}
        onSelectConversation={(id) => {
          loadConversation(id);
          setIsHistoryOpen(false);
        }}
        onNewChat={() => {
          startNewChat();
          setIsHistoryOpen(false);
        }}
      />

      {/* Voice & CosyVoice Settings Modal */}
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
    </div>
  );
};
export default App;
