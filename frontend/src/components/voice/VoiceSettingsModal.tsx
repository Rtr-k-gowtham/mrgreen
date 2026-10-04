import React, { useState } from 'react';
import { X, Sliders, Play } from 'lucide-react';
import {
  SupportedLanguage,
  SUPPORTED_LANGUAGES,
  VOICE_PROFILES,
  VoiceProfileId,
} from '../../types/voice';

interface VoiceSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  rate: number;
  onChangeRate: (rate: number) => void;
  language: SupportedLanguage;
  onChangeLanguage: (lang: SupportedLanguage) => void;
  voiceProfile?: VoiceProfileId;
  onChangeVoiceProfile?: (profile: VoiceProfileId) => void;
  onTestVoice?: (text: string) => void;
  voices?: SpeechSynthesisVoice[];
  selectedVoice?: SpeechSynthesisVoice | null;
  onSelectVoice?: (voice: SpeechSynthesisVoice) => void;
}

export const VoiceSettingsModal: React.FC<VoiceSettingsModalProps> = ({
  isOpen,
  onClose,
  voiceEnabled,
  onToggleVoice,
  rate,
  onChangeRate,
  language,
  onChangeLanguage,
  voiceProfile = 'GREEN_DEFAULT',
  onChangeVoiceProfile,
  onTestVoice,
}) => {
  const [pitch, setPitch] = useState<number>(1.0);

  if (!isOpen) return null;

  const handleTestVoice = () => {
    const testText =
      language === 'ta-IN'
        ? 'வணக்கம்! நான் MR.GREEN, உங்கள் தனிப்பட்ட உதவியாளர்.'
        : 'Hello! I am MR.GREEN, your private autonomous AI assistant.';
    if (onTestVoice) {
      onTestVoice(testText);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-sm bg-[#080d0a] border border-emerald-900/60 rounded-2xl shadow-2xl p-5 overflow-hidden text-zinc-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white tracking-wide font-mono">
              VOICE & COSYVOICE SETTINGS
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-lg"
            aria-label="Close settings"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Settings Body */}
        <div className="py-4 space-y-4 text-xs">
          {/* Custom MR.GREEN Voice Profile */}
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1 font-mono">
              CosyVoice Persona
            </label>
            <select
              value={voiceProfile}
              onChange={(e) => onChangeVoiceProfile?.(e.target.value as VoiceProfileId)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
            >
              {VOICE_PROFILES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.description}
                </option>
              ))}
            </select>
          </div>

          {/* Voice Response Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-zinc-200">Voice Synthesis (CosyVoice)</div>
              <div className="text-[11px] text-zinc-500">Play spoken responses aloud</div>
            </div>
            <button
              type="button"
              onClick={onToggleVoice}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                voiceEnabled ? 'bg-emerald-600' : 'bg-zinc-800'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform ${
                  voiceEnabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Speech Language */}
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1.5 font-mono">
              Language Mode
            </label>
            <select
              value={language}
              onChange={(e) => onChangeLanguage(e.target.value as SupportedLanguage)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label} ({lang.nativeLabel})
                </option>
              ))}
            </select>
          </div>

          {/* Speech Rate Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="font-medium text-zinc-300 font-mono">Speaking Speed</label>
              <span className="font-mono text-emerald-400">{rate.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.4"
              step="0.1"
              value={rate}
              onChange={(e) => onChangeRate(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
          </div>

          {/* Pitch Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="font-medium text-zinc-300 font-mono">Pitch</label>
              <span className="font-mono text-emerald-400">{pitch.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.2"
              step="0.1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
          </div>

          {/* Test Voice Button */}
          <div className="pt-1">
            <button
              type="button"
              onClick={handleTestVoice}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-zinc-900 hover:bg-emerald-950/70 border border-zinc-800 hover:border-emerald-500/40 text-emerald-400 font-mono text-xs transition-colors"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>TEST VOICE</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-zinc-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-medium text-white transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
