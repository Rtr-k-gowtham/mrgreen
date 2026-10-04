import React, { useState, useRef } from 'react';
import { Mic, MicOff, Send, Volume2, VolumeX, Square, Globe } from 'lucide-react';
import { SupportedLanguage, SUPPORTED_LANGUAGES } from '../../types/voice';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  speechSupported: boolean;
  onToggleListen: () => void;
  onStopSpeaking: () => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  activeLanguage: SupportedLanguage;
  onChangeLanguage: (lang: SupportedLanguage) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isListening,
  isSpeaking,
  isProcessing,
  speechSupported,
  onToggleListen,
  onStopSpeaking,
  voiceEnabled,
  onToggleVoice,
  activeLanguage,
  onChangeLanguage,
  disabled = false,
}) => {
  const [inputText, setInputText] = useState<string>('');
  const [showLangMenu, setShowLangMenu] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing || disabled) return;

    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full bg-zinc-950/90 backdrop-blur-lg border-t border-zinc-800/80 px-3 pt-2 pb-safe-bottom">
      {/* Top micro toolbar: Voice toggle, Language selector, Stop Speaking action */}
      <div className="flex items-center justify-between px-1 pb-2 text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          {/* Audio TTS toggle */}
          <button
            type="button"
            onClick={onToggleVoice}
            className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
              voiceEnabled
                ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                : 'bg-zinc-900 text-zinc-500 border border-zinc-800'
            }`}
            title={voiceEnabled ? 'Voice response enabled' : 'Voice response muted'}
            aria-label="Toggle voice output"
          >
            {voiceEnabled ? (
              <>
                <Volume2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Voice ON</span>
              </>
            ) : (
              <>
                <VolumeX className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Voice OFF</span>
              </>
            )}
          </button>

          {/* Stop Speaking button when TTS is playing */}
          {isSpeaking && (
            <button
              type="button"
              onClick={onStopSpeaking}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-500/40 animate-pulse"
              aria-label="Stop speaking"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop Speaking</span>
            </button>
          )}
        </div>

        {/* Language selector */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowLangMenu(!showLangMenu)}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-zinc-900 text-zinc-300 hover:text-white border border-zinc-800 text-[11px] font-mono transition-colors"
            aria-label="Select speech language"
          >
            <Globe className="w-3.5 h-3.5 text-emerald-400" />
            <span>{activeLanguage}</span>
          </button>

          {showLangMenu && (
            <div className="absolute right-0 bottom-full mb-1.5 w-40 bg-zinc-900 border border-zinc-750 rounded-xl shadow-xl z-50 overflow-hidden py-1">
              <div className="px-2.5 py-1 text-[10px] uppercase font-mono text-zinc-500 tracking-wider">
                Language
              </div>
              {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    onChangeLanguage(lang.code);
                    setShowLangMenu(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left text-xs flex items-center justify-between hover:bg-zinc-800 ${
                    activeLanguage === lang.code
                      ? 'text-emerald-400 font-semibold bg-zinc-800/50'
                      : 'text-zinc-300'
                  }`}
                >
                  <span>{lang.nativeLabel}</span>
                  <span className="font-mono text-[10px] text-zinc-500">{lang.code}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main input row: [Microphone Button] + [Text Input] + [Send Button] */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2 pb-1">
        {/* Microphone Button */}
        <button
          type="button"
          onClick={onToggleListen}
          disabled={disabled || !speechSupported}
          aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
          title={
            !speechSupported
              ? 'Speech recognition is not supported in this browser. You can still type.'
              : isListening
              ? 'Listening... tap to stop'
              : 'Tap microphone to speak'
          }
          className={`flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 ${
            !speechSupported
              ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed border border-zinc-800'
              : isListening
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/50 scale-105 animate-pulse'
              : 'bg-emerald-950/70 hover:bg-emerald-900/80 text-emerald-400 border border-emerald-500/40 active:scale-95'
          }`}
        >
          {isListening ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        {/* Text Input */}
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? 'Listening...' : 'Type a message...'}
            disabled={disabled || isProcessing}
            aria-label="Type message to MR.GREEN"
            className="w-full bg-zinc-900 border border-zinc-800 rounded-full px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/50 transition-all pr-10"
          />

          {/* Quick Clear / State */}
          {inputText && (
            <button
              type="button"
              onClick={() => setInputText('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs px-1"
            >
              ✕
            </button>
          )}
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputText.trim() || isProcessing || disabled}
          aria-label="Send message"
          className="flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white transition-all shadow-md active:scale-95"
        >
          <Send className="w-4 h-4 ml-0.5" />
        </button>
      </form>
    </div>
  );
};
