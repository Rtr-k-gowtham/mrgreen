export type OrbState =
  | 'IDLE'
  | 'LISTENING'
  | 'THINKING'
  | 'TOOL_EXECUTION'
  | 'SPEAKING'
  | 'ERROR'
  | 'OFFLINE';

export type SupportedLanguage = 'en-IN' | 'en-US' | 'ta-IN';

export interface LanguageOption {
  code: SupportedLanguage;
  label: string;
  nativeLabel: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en-IN', label: 'English (India)', nativeLabel: 'Indian English' },
  { code: 'en-US', label: 'English (US)', nativeLabel: 'US English' },
  { code: 'ta-IN', label: 'Tamil (India)', nativeLabel: 'தமிழ்' },
];

export interface VoiceSettings {
  autoSpeak: boolean;
  language: SupportedLanguage;
  rate: number;
  pitch: number;
  voiceURI: string | null;
}
