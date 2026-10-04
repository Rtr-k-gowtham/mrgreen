/**
 * MR.GREEN — Voice Types & State Specifications
 *
 * Adheres to Section 8 Voice Session States:
 * IDLE, CONNECTING, CONNECTED, LISTENING, USER_SPEAKING,
 * PROCESSING, THINKING, TOOL_EXECUTING, ASSISTANT_SPEAKING,
 * INTERRUPTED, ERROR, DISCONNECTED.
 */

export type VoiceState =
  | 'IDLE'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'LISTENING'
  | 'USER_SPEAKING'
  | 'PROCESSING'
  | 'THINKING'
  | 'TOOL_EXECUTING'
  | 'TOOL_EXECUTION'
  | 'ASSISTANT_SPEAKING'
  | 'SPEAKING'
  | 'INTERRUPTED'
  | 'ERROR'
  | 'DISCONNECTED'
  | 'OFFLINE';

// Backwards compatibility alias for test suites
export type OrbState = VoiceState;

export type SupportedLanguage = 'en-IN' | 'en-US' | 'ta-IN' | 'auto';

export interface LanguageOption {
  code: SupportedLanguage;
  label: string;
  nativeLabel: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'auto', label: 'Auto Detect', nativeLabel: 'Auto (English/தமிழ்)' },
  { code: 'en-IN', label: 'English (India)', nativeLabel: 'Indian English' },
  { code: 'en-US', label: 'English (US)', nativeLabel: 'US English' },
  { code: 'ta-IN', label: 'Tamil (India)', nativeLabel: 'தமிழ்' },
];

export type VoiceProfileId =
  | 'GREEN_DEFAULT'
  | 'GREEN_DEEP'
  | 'GREEN_CALM'
  | 'GREEN_TAMIL';

export interface VoiceProfileOption {
  id: VoiceProfileId;
  name: string;
  description: string;
}

export const VOICE_PROFILES: VoiceProfileOption[] = [
  { id: 'GREEN_DEFAULT', name: 'Green Default', description: 'Intelligent, balanced cyber assistant' },
  { id: 'GREEN_DEEP', name: 'Green Deep', description: 'Authoritative, resonant tone' },
  { id: 'GREEN_CALM', name: 'Green Calm', description: 'Soft, analytical cadence' },
  { id: 'GREEN_TAMIL', name: 'Green Tamil', description: 'Optimized for Tamil articulation' },
];

export interface VoiceSettings {
  autoSpeak: boolean;
  language: SupportedLanguage;
  voiceProfile: VoiceProfileId;
  rate: number;
  pitch: number;
  voiceURI: string | null;
}
