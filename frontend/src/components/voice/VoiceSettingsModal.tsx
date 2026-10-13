import React, { useState } from 'react';
import { X, Sliders, Play, CheckCircle2 } from 'lucide-react';
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
  const [conversationMode, setConversationMode] = useState<'continuous' | 'tap'>('tap');

  if (!isOpen) return null;

  const handleTestVoice = () => {
    const testText =
      language === 'ta-IN'
        ? 'வணக்கம்! நான் MR.GREEN, உங்கள் தனிப்பட்ட உதவியாளர்.'
        : 'Hello! I am MR.GREEN, your private assistant.';
    if (onTestVoice) {
      onTestVoice(testText);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-sm bg-white border border-slate-200 rounded-3xl shadow-2xl p-6 overflow-hidden text-slate-800">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-green-50 text-green-700 flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Settings
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-full hover:bg-slate-100 transition-colors"
            aria-label="Close settings"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Settings Body */}
        <div className="py-4 space-y-4 text-xs">
          {/* Custom MR.GREEN Voice Profile */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Assistant Voice Persona
            </label>
            <select
              value={voiceProfile}
              onChange={(e) => onChangeVoiceProfile?.(e.target.value as VoiceProfileId)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-green-500 focus:bg-white transition-colors"
            >
              {VOICE_PROFILES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.description}
                </option>
              ))}
            </select>
          </div>

          {/* Speech Language */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => onChangeLanguage(e.target.value as SupportedLanguage)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-green-500 focus:bg-white transition-colors"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label} ({lang.nativeLabel})
                </option>
              ))}
            </select>
          </div>

          {/* Conversation Mode */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Conversation Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setConversationMode('tap')}
                className={`py-1.5 px-3 rounded-xl border text-xs font-medium transition-all ${
                  conversationMode === 'tap'
                    ? 'bg-green-50 border-green-300 text-green-700'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                Tap to Talk
              </button>
              <button
                type="button"
                onClick={() => setConversationMode('continuous')}
                className={`py-1.5 px-3 rounded-xl border text-xs font-medium transition-all ${
                  conversationMode === 'continuous'
                    ? 'bg-green-50 border-green-300 text-green-700'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                Hands-free
              </button>
            </div>
          </div>

          {/* Speech Rate Slider */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="font-medium text-slate-700">Speaking Speed</label>
              <span className="font-mono text-green-600 font-semibold">{rate.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.4"
              step="0.1"
              value={rate}
              onChange={(e) => onChangeRate(parseFloat(e.target.value))}
              className="w-full accent-green-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
          </div>

          {/* Voice Synthesis Toggle */}
          <div className="flex items-center justify-between pt-1">
            <div>
              <div className="font-medium text-slate-800">Spoken Responses</div>
              <div className="text-[11px] text-slate-500">Read responses aloud using CosyVoice</div>
            </div>
            <button
              type="button"
              onClick={onToggleVoice}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                voiceEnabled ? 'bg-green-600' : 'bg-slate-200'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform ${
                  voiceEnabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Test Voice Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={handleTestVoice}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-slate-100 hover:bg-green-50 hover:text-green-700 text-slate-700 border border-slate-200 transition-colors font-medium text-xs"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Test Voice Preview</span>
            </button>
          </div>

          {/* Connection Status Section */}
          <div className="pt-3 border-t border-slate-100">
            <div className="text-[11px] font-medium text-slate-500 mb-1.5">Service Status</div>
            <div className="grid grid-cols-2 gap-1.5 text-[11px] text-slate-600">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-green-600" />
                <span>FastAPI Backend</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-green-600" />
                <span>CosyVoice TTS</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-100 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-green-600 hover:bg-green-700 text-xs font-semibold text-white transition-colors shadow-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
export default VoiceSettingsModal;
