import React from 'react';
import { X, Sliders } from 'lucide-react';
import { SupportedLanguage, SUPPORTED_LANGUAGES } from '../../types/voice';

interface VoiceSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  rate: number;
  onChangeRate: (rate: number) => void;
  language: SupportedLanguage;
  onChangeLanguage: (lang: SupportedLanguage) => void;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  onSelectVoice: (voice: SpeechSynthesisVoice) => void;
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
  voices,
  selectedVoice,
  onSelectVoice,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-5 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Voice & Speech Settings</h2>
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
        <div className="py-4 space-y-4">
          {/* Voice Response Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-zinc-200">Voice Response (TTS)</div>
              <div className="text-[11px] text-zinc-400">Read MR.GREEN responses aloud</div>
            </div>
            <button
              type="button"
              onClick={onToggleVoice}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                voiceEnabled ? 'bg-emerald-600' : 'bg-zinc-700'
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
            <label className="block text-xs font-medium text-zinc-200 mb-1.5">
              Spoken Language
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
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-zinc-200">Speech Rate</label>
              <span className="text-xs font-mono text-emerald-400">{rate.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.7"
              max="1.5"
              step="0.1"
              value={rate}
              onChange={(e) => onChangeRate(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-zinc-500 mt-1 font-mono">
              <span>Slower (0.7x)</span>
              <span>Normal (1.0x)</span>
              <span>Faster (1.5x)</span>
            </div>
          </div>

          {/* Voice selection (if browser has multiple voices) */}
          {voices.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-zinc-200 mb-1.5">
                Device Voice
              </label>
              <select
                value={selectedVoice?.voiceURI || ''}
                onChange={(e) => {
                  const found = voices.find((v) => v.voiceURI === e.target.value);
                  if (found) onSelectVoice(found);
                }}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-white truncate focus:outline-none focus:border-emerald-500"
              >
                {voices.map((v) => (
                  <option key={v.voiceURI} value={v.voiceURI}>
                    {v.name} ({v.lang})
                  </option>
                ))}
              </select>
            </div>
          )}
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
