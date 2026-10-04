import React, { useState, useRef } from 'react';
import { Mic, MicOff, Send, Volume2, VolumeX, Square, Globe } from 'lucide-react';
import { SupportedLanguage, SUPPORTED_LANGUAGES, VoiceState } from '../../types/voice';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  interimTranscript?: string;
  voiceState?: VoiceState;
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
  interimTranscript = '',
  voiceState: _voiceState,
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
    <div className="w-full bg-[#050806]/95 backdrop-blur-xl border-t border-emerald-950/60 px-3 pt-2 pb-safe-bottom shadow-2xl shadow-emerald-950/40">
      {/* Top HUD Status Row: Active status indicator, Voice toggle, Language selector, Stop Speaking action */}
      <div className="flex items-center justify-between px-1.5 pb-2 text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          {/* Subtle Live Voice State Badge */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-zinc-900/80 border border-zinc-800 text-[10px] font-mono">
            {isSpeaking ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="flex items-end gap-0.5 h-3">
                  <span className="w-0.5 bg-emerald-400 h-2 animate-audio-bar-1" />
                  <span className="w-0.5 bg-emerald-400 h-3 animate-audio-bar-2" />
                  <span className="w-0.5 bg-emerald-400 h-1.5 animate-audio-bar-3" />
                </span>
                <span>SPEAKING (COSYVOICE)</span>
              </span>
            ) : isListening ? (
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>LISTENING</span>
              </span>
            ) : isProcessing ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>THINKING</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 text-zinc-400">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                <span>READY</span>
              </span>
            )}
          </div>

          {/* Voice Response Mute/Unmute */}
          <button
            type="button"
            onClick={onToggleVoice}
            className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono transition-colors ${
              voiceEnabled
                ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-500/30'
                : 'bg-zinc-900 text-zinc-500 border border-zinc-800'
            }`}
            title={voiceEnabled ? 'Voice response enabled' : 'Voice response muted'}
            aria-label="Toggle voice output"
          >
            {voiceEnabled ? (
              <>
                <Volume2 className="w-3 h-3" />
                <span className="hidden sm:inline">VOICE ON</span>
              </>
            ) : (
              <>
                <VolumeX className="w-3 h-3" />
                <span className="hidden sm:inline">VOICE OFF</span>
              </>
            )}
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* Immediate Barge-in / Stop Speaking Action */}
          {isSpeaking && (
            <button
              type="button"
              onClick={onStopSpeaking}
              className="flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-500/50 hover:bg-rose-900 transition-colors animate-pulse"
              aria-label="Stop speaking"
              title="Interrupt speech immediately"
            >
              <Square className="w-2.5 h-2.5 fill-current" />
              <span>INTERRUPT</span>
            </button>
          )}

          {/* Language selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-zinc-900 text-zinc-300 hover:text-white border border-zinc-800 text-[10px] font-mono transition-colors"
              aria-label="Select speech language"
            >
              <Globe className="w-3 h-3 text-emerald-400" />
              <span>{activeLanguage.toUpperCase()}</span>
            </button>

            {showLangMenu && (
              <div className="absolute right-0 bottom-full mb-1.5 w-44 bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl z-50 overflow-hidden py-1">
                <div className="px-2.5 py-1 text-[10px] uppercase font-mono text-zinc-500 tracking-wider">
                  Voice Language
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
                        ? 'text-emerald-400 font-semibold bg-zinc-800/60'
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
      </div>

      {/* Main input composer: [Microphone Button] + [Interactive Input Container] + [Send Button] */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2 pb-1">
        {/* Futuristic Microphone Button */}
        <button
          type="button"
          onClick={onToggleListen}
          disabled={disabled}
          aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
          title={
            !speechSupported
              ? 'Click to start microphone input'
              : isListening
              ? 'Listening... tap to stop'
              : 'Tap to speak to MR.GREEN'
          }
          className={`flex-shrink-0 w-11 h-11 rounded-2xl flex items-center justify-center transition-all duration-300 ${
            isListening
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/50 scale-105 border border-emerald-400 animate-pulse'
              : 'bg-emerald-950/50 hover:bg-emerald-900/70 text-emerald-400 border border-emerald-500/30 hover:border-emerald-400/60 active:scale-95'
          }`}
        >
          {isListening ? (
            <MicOff className="w-5 h-5 text-black" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        {/* Text Input / Voice Status Field */}
        <div className="relative flex-1">
          {isListening ? (
            <div
              onClick={onToggleListen}
              className="w-full bg-[#08100b] border border-emerald-500/50 rounded-2xl px-4 py-2.5 text-sm text-emerald-300 flex items-center justify-between cursor-pointer shadow-inner shadow-emerald-950/60 animate-pulse"
            >
              <div className="flex items-center gap-2 overflow-hidden mr-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping flex-shrink-0" />
                <span className="font-mono text-xs text-emerald-300 truncate">
                  {interimTranscript || 'Listening... Speak naturally'}
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 flex-shrink-0">
                TAP TO STOP
              </span>
            </div>
          ) : isSpeaking ? (
            <div
              onClick={onStopSpeaking}
              className="w-full bg-[#08100b] border border-emerald-500/30 rounded-2xl px-4 py-2.5 text-sm text-emerald-200 flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span className="flex items-end gap-0.5 h-3">
                  <span className="w-0.5 bg-emerald-400 h-2 animate-audio-bar-1" />
                  <span className="w-0.5 bg-emerald-400 h-3 animate-audio-bar-2" />
                  <span className="w-0.5 bg-emerald-400 h-1.5 animate-audio-bar-3" />
                </span>
                <span className="font-mono text-xs text-emerald-300">MR.GREEN is speaking...</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/50">
                INTERRUPT
              </span>
            </div>
          ) : (
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message MR.GREEN... (English or தமிழ்)"
              disabled={disabled || isProcessing}
              aria-label="Type message to MR.GREEN"
              className="w-full bg-[#0a0f0d] border border-emerald-950 focus:border-emerald-500/50 rounded-2xl px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/40 transition-all pr-9 font-normal"
            />
          )}

          {/* Quick Clear */}
          {inputText && !isListening && !isSpeaking && (
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
          disabled={!inputText.trim() || isProcessing || disabled || isListening}
          aria-label="Send message"
          className="flex-shrink-0 w-11 h-11 rounded-2xl flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white transition-all shadow-md active:scale-95 border border-emerald-500/30"
        >
          <Send className="w-4 h-4 ml-0.5" />
        </button>
      </form>
    </div>
  );
};
