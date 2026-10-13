import React, { useState } from 'react';
import { Mic, MicOff, Square, Keyboard, Send, X } from 'lucide-react';

interface BottomVoiceControlProps {
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  speechSupported: boolean;
  onToggleListen: () => void;
  onStopSpeaking: () => void;
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export const BottomVoiceControl: React.FC<BottomVoiceControlProps> = ({
  isListening,
  isSpeaking,
  isProcessing,
  speechSupported,
  onToggleListen,
  onStopSpeaking,
  onSendMessage,
  disabled = false,
}) => {
  const [showTextInput, setShowTextInput] = useState<boolean>(false);
  const [typedText, setTypedText] = useState<string>('');

  const handleMainButtonClick = () => {
    if (isSpeaking) {
      onStopSpeaking();
    } else {
      onToggleListen();
    }
  };

  const handleSubmitText = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = typedText.trim();
    if (!clean || disabled) return;
    onSendMessage(clean);
    setTypedText('');
    setShowTextInput(false);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full px-4 pb-safe-bottom pt-2 select-none">
      {/* Discreet Single-Line Text Fallback Input (Revealed on demand) */}
      {showTextInput && (
        <form
          onSubmit={handleSubmitText}
          className="w-full max-w-md mb-4 flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-4 py-2 shadow-sm animate-fade-in transition-all"
        >
          <input
            type="text"
            value={typedText}
            onChange={(e) => setTypedText(e.target.value)}
            placeholder="Type a message to MR.GREEN..."
            className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            autoFocus
          />
          {typedText.trim() && (
            <button
              type="submit"
              disabled={disabled || isProcessing}
              className="p-1.5 rounded-full bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
              aria-label="Send message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setShowTextInput(false)}
            className="p-1 rounded-full text-slate-400 hover:text-slate-600 transition-colors"
            aria-label="Close text input"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </form>
      )}

      {/* Main Microphone Control Area with Waveforms on Both Sides */}
      <div className="flex items-center justify-center gap-4 sm:gap-6 relative">
        {/* Left Audio Waveform Bars (Active when listening or speaking) */}
        <div
          className={`flex items-center gap-1 h-10 w-12 justify-end transition-opacity duration-300 ${
            isListening || isSpeaking ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
          aria-hidden="true"
        >
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-1" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-2" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-3" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-4" />
        </div>

        {/* Prominent Circular Microphone Button */}
        <button
          type="button"
          onClick={handleMainButtonClick}
          disabled={disabled || (!speechSupported && !isSpeaking)}
          className={`relative rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-green-400/30 ${
            isSpeaking
              ? 'w-16 h-16 sm:w-20 sm:h-20 bg-rose-600 hover:bg-rose-700 shadow-xl shadow-rose-500/25 active:scale-95'
              : isListening
              ? 'w-18 h-18 sm:w-20 sm:h-20 bg-gradient-to-tr from-[#16A34A] to-[#22C55E] shadow-2xl shadow-green-500/40 ring-4 ring-green-300/60 active:scale-95'
              : 'w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-tr from-[#16A34A] to-[#22C55E] hover:from-[#15803D] hover:to-[#16A34A] shadow-xl shadow-green-500/25 hover:shadow-green-500/40 active:scale-95'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          aria-label={
            isSpeaking
              ? 'Stop speaking'
              : isListening
              ? 'Stop listening'
              : 'Start listening'
          }
          title={
            isSpeaking
              ? 'Interrupt speech'
              : isListening
              ? 'Tap to stop listening'
              : 'Tap to speak with MR.GREEN'
          }
        >
          {isSpeaking ? (
            <Square className="w-7 h-7 sm:w-8 sm:h-8 text-white fill-current" />
          ) : !speechSupported ? (
            <MicOff className="w-7 h-7 sm:w-8 sm:h-8 text-white" />
          ) : (
            <Mic
              className={`w-7 h-7 sm:w-8 sm:h-8 text-white transition-transform ${
                isListening ? 'scale-110' : ''
              }`}
            />
          )}
        </button>

        {/* Right Audio Waveform Bars (Active when listening or speaking) */}
        <div
          className={`flex items-center gap-1 h-10 w-12 justify-start transition-opacity duration-300 ${
            isListening || isSpeaking ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
          aria-hidden="true"
        >
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-4" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-3" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-2" />
          <span className="w-1 bg-green-500 rounded-full animate-audio-bar-1" />
        </div>

        {/* Discreet Text Input Fallback Toggle Button */}
        <button
          type="button"
          onClick={() => setShowTextInput((prev) => !prev)}
          className={`absolute -right-12 sm:-right-14 p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors ${
            showTextInput ? 'text-green-600 bg-green-50' : ''
          }`}
          aria-label="Toggle text entry fallback"
          title="Type message instead"
        >
          <Keyboard className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
export default BottomVoiceControl;
