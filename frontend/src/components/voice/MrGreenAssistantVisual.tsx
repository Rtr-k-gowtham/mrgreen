import React from 'react';
import { VoiceState } from '../../types/voice';
import { RotateCcw } from 'lucide-react';

interface MrGreenAssistantVisualProps {
  voiceState: VoiceState;
  isListening?: boolean;
  isSpeaking?: boolean;
  isProcessing?: boolean;
  isOnline?: boolean;
  interimTranscript?: string;
  lastResponse?: string;
  onRetry?: () => void;
}

export const MrGreenAssistantVisual: React.FC<MrGreenAssistantVisualProps> = ({
  voiceState,
  isListening = false,
  isSpeaking = false,
  isProcessing = false,
  isOnline = true,
  interimTranscript,
  lastResponse,
  onRetry,
}) => {
  // Determine dominant mode for visual state
  const isError = !isOnline || voiceState === 'ERROR' || voiceState === 'DISCONNECTED' || voiceState === 'OFFLINE';
  const isActualListening = isListening || voiceState === 'LISTENING' || voiceState === 'USER_SPEAKING';
  const isActualThinking = isProcessing || voiceState === 'THINKING' || voiceState === 'PROCESSING' || voiceState === 'TOOL_EXECUTING' || voiceState === 'TOOL_EXECUTION';
  const isActualSpeaking = isSpeaking || voiceState === 'ASSISTANT_SPEAKING' || voiceState === 'SPEAKING';

  // Dynamic status text
  const getStatusText = (): string => {
    if (isError) return 'Connection issue';
    if (isActualListening) return 'Listening...';
    if (isActualThinking) return 'Thinking...';
    if (isActualSpeaking) return 'Speaking...';
    return 'Ready when you are';
  };

  const statusText = getStatusText();

  // Secondary caption: interim transcript while listening, or subtle response snippet
  const captionText = isActualListening
    ? (interimTranscript ? `"${interimTranscript}"` : '')
    : (isActualSpeaking && lastResponse ? lastResponse : '');

  return (
    <div className="flex flex-col items-center justify-center select-none w-full max-w-md mx-auto px-4 py-8">
      {/* Central AI Visual Canvas (SVG + CSS) */}
      <div className="relative w-64 h-64 sm:w-72 sm:h-72 flex items-center justify-center">
        {/* Ambient Soft Green Halo Glow */}
        <div
          className={`absolute inset-4 rounded-full transition-all duration-700 pointer-events-none ${
            isError
              ? 'bg-rose-100/50 blur-2xl scale-95'
              : isActualListening
              ? 'bg-green-200/60 blur-3xl scale-110 animate-ring-expand'
              : isActualThinking
              ? 'bg-emerald-200/50 blur-2xl scale-105 animate-pulse'
              : isActualSpeaking
              ? 'bg-green-300/60 blur-3xl scale-110 animate-wave-pulse'
              : 'bg-green-100/40 blur-2xl scale-100 animate-jarvis-breathe'
          }`}
          aria-hidden="true"
        />

        {/* Concentric Precision SVG Rings & AI Core */}
        <svg
          viewBox="0 0 320 320"
          className={`w-full h-full relative z-10 transition-transform duration-700 ${
            isActualListening
              ? 'animate-ring-expand'
              : isActualThinking
              ? 'scale-105'
              : isActualSpeaking
              ? 'animate-wave-pulse'
              : 'animate-jarvis-breathe'
          }`}
          aria-label={`MR.GREEN Assistant state: ${statusText}`}
          role="img"
        >
          <defs>
            {/* Core Gradient */}
            <linearGradient id="mgCoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#22C55E" />
              <stop offset="100%" stopColor="#16A34A" />
            </linearGradient>

            {/* Error Gradient */}
            <linearGradient id="mgErrorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F87171" />
              <stop offset="100%" stopColor="#DC2626" />
            </linearGradient>

            {/* Soft Ambient Inner Glow */}
            <radialGradient id="mgInnerHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22C55E" stopOpacity="0.25" />
              <stop offset="70%" stopColor="#16A34A" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#16A34A" stopOpacity="0" />
            </radialGradient>

            {/* Core Drop Shadow */}
            <filter id="mgCoreShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow
                dx="0"
                dy="6"
                stdDeviation="8"
                floodColor="#16A34A"
                floodOpacity="0.22"
              />
            </filter>
          </defs>

          {/* Outermost Precision Orbit Ring (Dashed) */}
          <circle
            cx="160"
            cy="160"
            r="142"
            fill="none"
            stroke={isError ? '#FECDD3' : '#DCFCE7'}
            strokeWidth="1.2"
            strokeDasharray="4 8"
            className="transition-colors duration-500"
          />

          {/* Secondary Concentric Gyroscope Ring (Rotates when processing/thinking) */}
          <g className={isActualThinking ? 'animate-gyro-spin origin-center' : ''}>
            <circle
              cx="160"
              cy="160"
              r="120"
              fill="none"
              stroke={isError ? '#FDA4AF' : isActualThinking ? '#22C55E' : '#BBF7D0'}
              strokeWidth={isActualThinking ? '2' : '1.2'}
              strokeDasharray={isActualThinking ? '28 14' : 'none'}
              opacity="0.85"
              className="transition-all duration-500"
            />
            {/* Small Orbit Nodes on the Gyro Ring */}
            {isActualThinking && (
              <>
                <circle cx="160" cy="40" r="3.5" fill="#16A34A" />
                <circle cx="160" cy="280" r="3.5" fill="#16A34A" />
                <circle cx="40" cy="160" r="3.5" fill="#22C55E" />
                <circle cx="280" cy="160" r="3.5" fill="#22C55E" />
              </>
            )}
          </g>

          {/* Counter-rotating Gyro Ring */}
          <g className={isActualThinking ? 'animate-gyro-reverse origin-center' : ''}>
            <circle
              cx="160"
              cy="160"
              r="98"
              fill="none"
              stroke={isError ? '#F43F5E' : '#86EFAC'}
              strokeWidth="1.2"
              strokeDasharray={isActualThinking ? '16 8' : 'none'}
              opacity={isActualListening ? '0.9' : '0.55'}
              className="transition-all duration-500"
            />
          </g>

          {/* Inner Halo Fill */}
          <circle
            cx="160"
            cy="160"
            r="82"
            fill={isError ? '#FFE4E6' : 'url(#mgInnerHalo)'}
            className="transition-colors duration-500"
          />

          {/* Live Waveform Rings (Expands during listening or pulses during speaking) */}
          {isActualListening && (
            <circle
              cx="160"
              cy="160"
              r="86"
              fill="none"
              stroke="#22C55E"
              strokeWidth="2.5"
              strokeDasharray="6 6"
              className="animate-spin-slow origin-center"
            />
          )}

          {isActualSpeaking && (
            <circle
              cx="160"
              cy="160"
              r="88"
              fill="none"
              stroke="#16A34A"
              strokeWidth="2"
              opacity="0.7"
              className="animate-wave-pulse origin-center"
            />
          )}

          {/* Central AI Core Capsule */}
          <circle
            cx="160"
            cy="160"
            r="60"
            fill={isError ? 'url(#mgErrorGrad)' : 'url(#mgCoreGrad)'}
            filter="url(#mgCoreShadow)"
            className="transition-all duration-500"
          />

          {/* Inner Accent Ring inside Core */}
          <circle
            cx="160"
            cy="160"
            r="54"
            fill="none"
            stroke="rgba(255, 255, 255, 0.28)"
            strokeWidth="1.5"
          />

          {/* Center Mascot / AI Identity Emblem: Stylized MG Monogram with Leaf Motif */}
          <g transform="translate(160, 160)" className="text-white fill-white">
            {/* Minimal Leaf Symbol Accent at Top Center */}
            <path
              d="M 0 -36 C 9 -44, 20 -38, 22 -28 C 12 -26, 4 -30, 0 -36 Z"
              fill="#DCFCE7"
              opacity="0.95"
            />
            <path
              d="M 2 -34 Q 10 -31, 18 -29"
              stroke="#16A34A"
              strokeWidth="1"
              strokeLinecap="round"
              fill="none"
            />

            {/* Futuristic Geometric 'M' Letter */}
            <path
              d="M -30 18 L -30 -14 L -18 2 L -6 -14 L -6 18"
              stroke="#FFFFFF"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />

            {/* Futuristic Geometric 'G' Letter */}
            <path
              d="M 28 -6 C 24 -14, 12 -16, 4 -9 C -4 -2, -3 12, 5 17 C 14 21, 28 17, 28 8 L 15 8"
              stroke="#FFFFFF"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </g>
        </svg>
      </div>

      {/* Dynamic Status Text */}
      <div className="mt-5 flex flex-col items-center text-center">
        <p
          className={`text-sm sm:text-base font-medium tracking-tight transition-colors duration-300 ${
            isError
              ? 'text-rose-600'
              : isActualListening
              ? 'text-green-600 font-semibold'
              : isActualThinking
              ? 'text-green-700 font-medium'
              : isActualSpeaking
              ? 'text-green-600 font-medium'
              : 'text-slate-500'
          }`}
        >
          {statusText}
        </p>

        {/* Discreet Secondary Caption (Interim transcription or spoken response) */}
        {captionText && (
          <p className="mt-2 text-xs sm:text-sm text-slate-500 max-w-sm line-clamp-2 px-3 py-1 bg-slate-50 rounded-full border border-slate-100 transition-all duration-300 animate-fade-in font-normal">
            {captionText}
          </p>
        )}

        {/* Discreet Retry Button when Connection Error */}
        {isError && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry connection</span>
          </button>
        )}
      </div>
    </div>
  );
};
export default MrGreenAssistantVisual;
