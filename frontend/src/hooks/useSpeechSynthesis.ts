import { useState, useEffect, useRef, useCallback } from 'react';
import { SupportedLanguage } from '../types/voice';

export interface UseSpeechSynthesisOptions {
  defaultLanguage?: SupportedLanguage;
  defaultRate?: number;
  autoSpeak?: boolean;
}

export function useSpeechSynthesis({
  defaultLanguage = 'en-IN',
  defaultRate = 1.0,
  autoSpeak = true,
}: UseSpeechSynthesisOptions = {}) {
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [voiceEnabled, setVoiceEnabled] = useState<boolean>(autoSpeak);
  const [rate, setRate] = useState<number>(defaultRate);
  const [language, setLanguage] = useState<SupportedLanguage>(defaultLanguage);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Check support and populate voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);

      const updateVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices();
        setVoices(availableVoices);

        // Find appropriate voice for initial language
        const matched = availableVoices.find(
          (v) => v.lang === language || v.lang.replace('_', '-').startsWith(language)
        );
        if (matched) {
          setSelectedVoice(matched);
        } else if (availableVoices.length > 0) {
          setSelectedVoice(availableVoices[0]);
        }
      };

      updateVoices();

      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = updateVoices;
      }
    } else {
      setIsSupported(false);
    }
  }, [language]);

  // Clean text for speech: remove code blocks, raw markdown, excessive URLs
  const cleanTextForSpeech = (rawText: string): string => {
    let text = rawText;

    // Remove code blocks ```...```
    text = text.replace(/```[\s\S]*?```/g, ' [Code omitted] ');

    // Remove inline code `...`
    text = text.replace(/`([^`]+)`/g, '$1');

    // Remove markdown links [text](url) -> text
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

    // Remove bold / italic symbols
    text = text.replace(/[*_#~]/g, '');

    // Collapse multiple whitespaces
    text = text.replace(/\s+/g, ' ').trim();

    // Do not read excessively long technical responses (> 400 chars, limit to first 2-3 sentences)
    if (text.length > 350) {
      const sentences = text.match(/[^.!?]+[.!?]+/g);
      if (sentences && sentences.length > 0) {
        text = sentences.slice(0, 3).join(' ') + ' More details are available in the text.';
      } else {
        text = text.substring(0, 350) + '... Check the screen for full details.';
      }
    }

    return text;
  };

  const stop = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // ignore
      }
      setIsSpeaking(false);
      setIsPaused(false);
    }
  }, []);

  const pause = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window && isSpeaking) {
      try {
        window.speechSynthesis.pause();
        setIsPaused(true);
      } catch {
        // ignore
      }
    }
  }, [isSpeaking]);

  const resume = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window && isPaused) {
      try {
        window.speechSynthesis.resume();
        setIsPaused(false);
      } catch {
        // ignore
      }
    }
  }, [isPaused]);

  const speak = useCallback(
    (textToSpeak: string) => {
      if (!isSupported || !voiceEnabled || !textToSpeak.trim()) {
        return;
      }

      // Stop any active speech first
      stop();

      const cleaned = cleanTextForSpeech(textToSpeak);
      if (!cleaned) return;

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utteranceRef.current = utterance;

      utterance.lang = language;
      utterance.rate = rate;

      if (selectedVoice) {
        utterance.voice = selectedVoice;
      } else {
        // Try to match by language
        const matched = voices.find(
          (v) => v.lang === language || v.lang.replace('_', '-').startsWith(language)
        );
        if (matched) {
          utterance.voice = matched;
        }
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
      };

      utterance.onerror = (e) => {
        if (e.error !== 'canceled' && e.error !== 'interrupted') {
          console.warn('Speech synthesis error:', e.error);
        }
        setIsSpeaking(false);
        setIsPaused(false);
      };

      try {
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('Failed to invoke speech synthesis:', err);
        setIsSpeaking(false);
      }
    },
    [isSupported, voiceEnabled, language, rate, selectedVoice, voices, stop]
  );

  return {
    isSupported,
    isSpeaking,
    isPaused,
    voices,
    selectedVoice,
    setSelectedVoice,
    voiceEnabled,
    setVoiceEnabled,
    rate,
    setRate,
    language,
    setLanguage,
    speak,
    stop,
    pause,
    resume,
  };
}
