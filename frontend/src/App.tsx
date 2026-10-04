import React, { useState } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/layout/Header';
import { HistoryDrawer } from './components/layout/HistoryDrawer';
import { GreenOrb } from './components/voice/GreenOrb';
import { ChatList } from './components/chat/ChatList';
import { ChatInput } from './components/chat/ChatInput';
import { VoiceSettingsModal } from './components/voice/VoiceSettingsModal';

export const App: React.FC = () => {
  const {
    messages,
    conversationId,
    isOnline,
    isProcessing,
    orbState,
    errorMessage,
    activeLanguage,
    setActiveLanguage,
    stt,
    tts,
    sendMessage,
    startNewChat,
    loadConversation,
  } = useChat();

  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Toggle listening from orb or mic button
  const handleToggleListening = () => {
    if (stt.isListening) {
      stt.stopListening();
    } else {
      // If speaking, stop speaking first
      if (tts.isSpeaking) {
        tts.stop();
      }
      stt.startListening();
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-dark-950 text-white overflow-hidden">
      {/* Top Header */}
      <Header
        isOnline={isOnline}
        onNewChat={startNewChat}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 flex flex-col min-h-0 max-w-3xl w-full mx-auto relative overflow-hidden">
        {/* Animated Central GREEN CORE Orb */}
        <section
          aria-label="MR.GREEN Core Orb"
          className="flex-shrink-0 transition-all duration-300"
        >
          <GreenOrb
            state={orbState}
            interimTranscript={stt.interimTranscript}
            onToggleListen={handleToggleListening}
            isListening={stt.isListening}
            disabled={!stt.isSupported || !isOnline}
          />
        </section>

        {/* Global Error Banner (if any) */}
        {errorMessage && (
          <div className="px-4 py-1.5 flex-shrink-0">
            <div className="bg-rose-950/80 border border-rose-800 text-rose-200 text-xs px-3 py-1.5 rounded-xl flex items-center justify-between">
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Conversation Message List */}
        <section
          aria-label="Conversation messages"
          className="flex-1 min-h-0 flex flex-col overflow-hidden"
        >
          <ChatList
            messages={messages}
            isProcessing={isProcessing}
            onSelectPrompt={sendMessage}
            onSpeak={(text) => tts.speak(text)}
          />
        </section>

        {/* Bottom Input Area */}
        <footer className="flex-shrink-0">
          <ChatInput
            onSendMessage={sendMessage}
            isListening={stt.isListening}
            isSpeaking={tts.isSpeaking}
            isProcessing={isProcessing}
            speechSupported={stt.isSupported}
            onToggleListen={handleToggleListening}
            onStopSpeaking={tts.stop}
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
        onSelectConversation={loadConversation}
        onNewChat={startNewChat}
      />

      {/* Voice & Speech Settings Modal */}
      <VoiceSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        voiceEnabled={tts.voiceEnabled}
        onToggleVoice={() => tts.setVoiceEnabled(!tts.voiceEnabled)}
        rate={tts.rate}
        onChangeRate={tts.setRate}
        language={activeLanguage}
        onChangeLanguage={setActiveLanguage}
        voices={tts.voices}
        selectedVoice={tts.selectedVoice}
        onSelectVoice={tts.setSelectedVoice}
      />
    </div>
  );
};

export default App;
