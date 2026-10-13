/**
 * MR.GREEN — Voice Diagnostic Panel (Development Only)
 *
 * Shows real-time voice pipeline state for debugging:
 * - Microphone / STT status
 * - WebSocket connection status
 * - Backend processing state
 * - TTS playback state
 * - Recent diagnostic events
 */

import React, { useState } from 'react';
import { VoiceState } from '../../types/voice';
import { VoiceDiagnosticEvent } from '../../services/voiceSocket';

interface VoiceDiagnosticPanelProps {
  voiceState: VoiceState;
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  isOnline: boolean;
  sttError: string | null;
  diagnosticEvents: VoiceDiagnosticEvent[];
}

export const VoiceDiagnosticPanel: React.FC<VoiceDiagnosticPanelProps> = ({
  voiceState,
  isListening,
  isSpeaking,
  isProcessing,
  isOnline,
  sttError,
  diagnosticEvents,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // Only render in development
  if (
    typeof import.meta !== 'undefined' &&
    import.meta.env?.PROD
  ) {
    return null;
  }

  const stateColor = (state: VoiceState): string => {
    switch (state) {
      case 'LISTENING':
      case 'USER_SPEAKING':
        return 'text-emerald-400';
      case 'THINKING':
      case 'PROCESSING':
      case 'TOOL_EXECUTING':
        return 'text-amber-400';
      case 'ASSISTANT_SPEAKING':
        return 'text-cyan-400';
      case 'ERROR':
        return 'text-rose-400';
      case 'OFFLINE':
      case 'DISCONNECTED':
        return 'text-zinc-500';
      default:
        return 'text-zinc-300';
    }
  };

  const levelColor = (level: string): string => {
    switch (level) {
      case 'error':
        return 'text-rose-400';
      case 'warn':
        return 'text-amber-400';
      default:
        return 'text-zinc-400';
    }
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-3 left-3 z-[9999] px-2 py-1 rounded-lg bg-zinc-900/90 border border-zinc-700 text-[10px] font-mono text-zinc-400 hover:text-emerald-400 hover:border-emerald-500/50 transition-colors"
        title="Open Voice Diagnostic Panel"
      >
        🔊 DIAG
      </button>
    );
  }

  const recentEvents = diagnosticEvents.slice(-20).reverse();

  return (
    <div className="fixed bottom-3 left-3 z-[9999] w-80 max-h-[60vh] bg-zinc-950/95 border border-zinc-700 rounded-xl shadow-2xl shadow-black/60 font-mono text-[10px] flex flex-col overflow-hidden backdrop-blur-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-800 bg-zinc-900/80 flex-shrink-0">
        <span className="text-emerald-400 font-bold tracking-wider">
          🔊 VOICE DIAGNOSTICS
        </span>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="text-zinc-500 hover:text-white transition-colors px-1"
        >
          ✕
        </button>
      </div>

      {/* State Summary */}
      <div className="px-3 py-2 border-b border-zinc-800 space-y-1 flex-shrink-0">
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">Voice State:</span>
          <span className={`font-bold ${stateColor(voiceState)}`}>
            {voiceState}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">Backend:</span>
          <span className={isOnline ? 'text-emerald-400' : 'text-rose-400'}>
            {isOnline ? '● ONLINE' : '○ OFFLINE'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">Microphone:</span>
          <span className={isListening ? 'text-emerald-400' : 'text-zinc-500'}>
            {isListening ? '● ACTIVE' : '○ IDLE'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">STT:</span>
          <span className={sttError ? 'text-rose-400' : 'text-zinc-500'}>
            {sttError ? `⚠ ${sttError.substring(0, 40)}` : 'OK'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">Processing:</span>
          <span
            className={isProcessing ? 'text-amber-400' : 'text-zinc-500'}
          >
            {isProcessing ? '● ACTIVE' : '○ IDLE'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-zinc-500">TTS:</span>
          <span className={isSpeaking ? 'text-cyan-400' : 'text-zinc-500'}>
            {isSpeaking ? '● SPEAKING' : '○ SILENT'}
          </span>
        </div>
      </div>

      {/* Event Log */}
      <div className="flex-1 min-h-0 overflow-y-auto px-3 py-1.5 space-y-0.5">
        {recentEvents.length === 0 ? (
          <div className="text-zinc-600 text-center py-4">
            No events yet. Start speaking.
          </div>
        ) : (
          recentEvents.map((e, i) => (
            <div key={`${e.timestamp}-${i}`} className="flex gap-1.5">
              <span className="text-zinc-600 flex-shrink-0 tabular-nums">
                {new Date(e.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </span>
              <span className={`flex-shrink-0 ${levelColor(e.level)}`}>
                [{e.stage}]
              </span>
              <span className="text-zinc-400 truncate">{e.detail}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
