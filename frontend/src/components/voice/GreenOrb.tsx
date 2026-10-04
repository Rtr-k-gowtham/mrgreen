import React from 'react';
import { OrbState } from '../../types/voice';
import { Mic, Volume2, Sparkles, AlertCircle, WifiOff, Cpu } from 'lucide-react';

interface GreenOrbProps {
  state: OrbState;
  interimTranscript?: string;
  onToggleListen?: () => void;
  isListening?: boolean;
  disabled?: boolean;
}

export const GreenOrb: React.FC<GreenOrbProps> = ({
  state,
  interimTranscript,
  onToggleListen,
  isListening,
  disabled = false,
}) => {
  const getOrbStateDetails = () => {
    switch (state) {
      case 'LISTENING':
        return {
          label: 'LISTENING...',
          subLabel: 'Speak clearly into your microphone',
          color: 'emerald',
          icon: Mic,
          pulseClass: 'animate-ping-slow scale-110 shadow-emerald-500/50',
          ringClass: 'border-emerald-400 animate-pulse',
          coreGradient: 'from-emerald-400 via-emerald-500 to-green-600',
        };
      case 'THINKING':
        return {
          label: 'THINKING...',
          subLabel: 'MR.GREEN is processing your request',
          color: 'teal',
          icon: Sparkles,
          pulseClass: 'scale-100 shadow-teal-500/40',
          ringClass: 'border-teal-400/80 animate-spin-slow border-t-transparent',
          coreGradient: 'from-teal-300 via-emerald-500 to-teal-700',
        };
      case 'TOOL_EXECUTION':
        return {
          label: 'EXECUTING TOOL...',
          subLabel: 'Running autonomous tool action',
          color: 'cyan',
          icon: Cpu,
          pulseClass: 'scale-105 shadow-cyan-500/50 animate-pulse',
          ringClass: 'border-cyan-400 animate-spin-reverse border-dashed',
          coreGradient: 'from-cyan-400 via-emerald-500 to-cyan-700',
        };
      case 'SPEAKING':
        return {
          label: 'SPEAKING...',
          subLabel: 'Tap stop button to silence',
          color: 'green',
          icon: Volume2,
          pulseClass: 'scale-105 shadow-green-400/60 animate-bounce-subtle',
          ringClass: 'border-emerald-300 animate-ping-slow',
          coreGradient: 'from-green-300 via-emerald-400 to-emerald-600',
        };
      case 'ERROR':
        return {
          label: 'ATTENTION',
          subLabel: 'Check connection or error details',
          color: 'rose',
          icon: AlertCircle,
          pulseClass: 'scale-95 shadow-rose-500/40',
          ringClass: 'border-rose-500/80',
          coreGradient: 'from-rose-500 via-red-600 to-rose-800',
        };
      case 'OFFLINE':
        return {
          label: 'OFFLINE',
          subLabel: 'Cannot reach backend server',
          color: 'slate',
          icon: WifiOff,
          pulseClass: 'opacity-40 grayscale',
          ringClass: 'border-zinc-700',
          coreGradient: 'from-zinc-600 via-zinc-700 to-zinc-900',
        };
      case 'IDLE':
      default:
        return {
          label: 'READY',
          subLabel: 'Tap to speak or type a message',
          color: 'emerald',
          icon: Mic,
          pulseClass: 'animate-breathe shadow-emerald-500/30',
          ringClass: 'border-emerald-500/30',
          coreGradient: 'from-emerald-400/90 via-emerald-600/80 to-emerald-900/90',
        };
    }
  };

  const details = getOrbStateDetails();
  const IconComponent = details.icon;

  return (
    <div className="flex flex-col items-center justify-center py-4 px-2 select-none">
      {/* Orb Container */}
      <div className="relative flex items-center justify-center w-40 h-40 sm:w-44 sm:h-44">
        {/* Outer Aura Glow */}
        <div
          className={`absolute inset-0 rounded-full blur-2xl opacity-40 transition-all duration-700 bg-gradient-to-tr ${details.coreGradient} ${details.pulseClass}`}
        />

        {/* Outer Geometric Ring */}
        <div
          className={`absolute -inset-2.5 rounded-full border-2 transition-all duration-700 pointer-events-none ${details.ringClass}`}
        />

        {/* Secondary Subtle Ring */}
        <div className="absolute -inset-1 rounded-full border border-emerald-500/20 pointer-events-none" />

        {/* Interactive Orb Core Button */}
        <button
          type="button"
          onClick={onToggleListen}
          disabled={disabled || state === 'OFFLINE'}
          aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
          className={`relative z-10 w-28 h-28 sm:w-32 sm:h-32 rounded-full flex flex-col items-center justify-center 
            bg-gradient-to-br ${details.coreGradient} 
            shadow-2xl transition-all duration-500 
            hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-500/40
            ${details.pulseClass}`}
        >
          {/* Audio reactive simulation wave bars when speaking */}
          {state === 'SPEAKING' ? (
            <div className="flex items-center gap-1 h-8">
              <span className="w-1 bg-white rounded-full animate-audio-bar-1 h-3" />
              <span className="w-1 bg-white rounded-full animate-audio-bar-2 h-7" />
              <span className="w-1 bg-white rounded-full animate-audio-bar-3 h-5" />
              <span className="w-1 bg-white rounded-full animate-audio-bar-2 h-8" />
              <span className="w-1 bg-white rounded-full animate-audio-bar-1 h-4" />
            </div>
          ) : (
            <IconComponent
              className={`w-10 h-10 text-white drop-shadow-md transition-transform duration-300 ${
                isListening ? 'scale-110' : ''
              }`}
            />
          )}

          {/* Inner Gloss Highlights */}
          <div className="absolute top-2 left-4 right-4 h-6 rounded-full bg-gradient-to-b from-white/30 to-transparent pointer-events-none" />
        </button>
      </div>

      {/* State Label & Sublabel */}
      <div className="mt-3 text-center flex flex-col items-center max-w-xs transition-opacity duration-300">
        <span className="text-xs sm:text-sm font-semibold tracking-wider text-emerald-400 uppercase font-mono flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              state === 'ERROR'
                ? 'bg-rose-500'
                : state === 'OFFLINE'
                ? 'bg-zinc-600'
                : 'bg-emerald-400 animate-pulse'
            }`}
          />
          {details.label}
        </span>

        {/* Live Interim Transcript or Subtitle */}
        {interimTranscript ? (
          <p className="text-xs sm:text-sm text-emerald-200 mt-1 italic line-clamp-2 px-3 py-1 bg-emerald-950/60 rounded-full border border-emerald-500/30 animate-fade-in max-w-xs">
            "{interimTranscript}"
          </p>
        ) : (
          <p className="text-[11px] sm:text-xs text-zinc-400 mt-0.5 line-clamp-1">
            {details.subLabel}
          </p>
        )}
      </div>
    </div>
  );
};
