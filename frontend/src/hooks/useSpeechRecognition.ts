import { useState, useEffect, useRef, useCallback } from 'react';
import { SupportedLanguage } from '../types/voice';

// Type definitions for Web Speech API
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

export interface UseSpeechRecognitionOptions {
  language?: SupportedLanguage;
  onFinalResult?: (transcript: string) => void;
  onError?: (errorMsg: string) => void;
}

export function useSpeechRecognition({
  language = 'en-IN',
  onFinalResult,
  onError,
}: UseSpeechRecognitionOptions = {}) {
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const isStoppingExplicitly = useRef<boolean>(false);

  // Detect support on mount
  useEffect(() => {
    const win = typeof window !== 'undefined' ? (window as IWindow) : null;
    const SpeechRecognitionClass = win?.SpeechRecognition || win?.webkitSpeechRecognition;

    if (SpeechRecognitionClass) {
      setIsSupported(true);
    } else {
      setIsSupported(false);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      isStoppingExplicitly.current = true;
      try {
        recognitionRef.current.stop();
      } catch {
        // Recognition might already be stopped
      }
      setIsListening(false);
    }
  }, [isListening]);

  const startListening = useCallback(() => {
    setError(null);
    setTranscript('');
    setInterimTranscript('');
    isStoppingExplicitly.current = false;

    const win = typeof window !== 'undefined' ? (window as IWindow) : null;
    const SpeechRecognitionClass = win?.SpeechRecognition || win?.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      const err = 'Speech recognition is not supported in this browser. Please use text input.';
      setError(err);
      onError?.(err);
      return;
    }

    try {
      // Abort any previous instance
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }

      const recognition = new SpeechRecognitionClass();
      recognition.lang = language;
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results[i];
          const text = result[0].transcript;

          if (result.isFinal) {
            final += text;
          } else {
            interim += text;
          }
        }

        if (interim) {
          setInterimTranscript(interim);
        }

        if (final) {
          const trimmedFinal = final.trim();
          setTranscript(trimmedFinal);
          setInterimTranscript('');
          onFinalResult?.(trimmedFinal);
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        let errorMessage = 'Voice recognition error occurred.';
        switch (event.error) {
          case 'not-allowed':
          case 'permission-denied':
            errorMessage = 'Microphone permission denied. Please allow microphone access.';
            break;
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'network':
            errorMessage = 'Network error during speech recognition.';
            break;
          case 'aborted':
            return; // Normal abort, no need to alert
          default:
            errorMessage = `Voice recognition error: ${event.error}`;
        }

        setError(errorMessage);
        onError?.(errorMessage);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e: any) {
      const err = e?.message || 'Failed to start microphone.';
      setError(err);
      onError?.(err);
      setIsListening(false);
    }
  }, [language, onFinalResult, onError]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  return {
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    error,
    startListening,
    stopListening,
    resetTranscript: () => {
      setTranscript('');
      setInterimTranscript('');
    },
  };
}
