import { useState, useEffect, useRef, useCallback } from 'react';
import { SupportedLanguage } from '../types/voice';

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
  const [isSupported, setIsSupported] = useState<boolean>(true);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const isStoppingExplicitly = useRef<boolean>(false);
  const latestTranscriptRef = useRef<string>('');
  const hasSubmittedRef = useRef<boolean>(false);
  const silenceTimerRef = useRef<any>(null);
  const onFinalResultRef = useRef(onFinalResult);
  const onErrorRef = useRef(onError);

  onFinalResultRef.current = onFinalResult;
  onErrorRef.current = onError;

  // Detect support on mount
  useEffect(() => {
    const win = typeof window !== 'undefined' ? (window as IWindow) : null;
    const hasSpeechClass = Boolean(win?.SpeechRecognition || win?.webkitSpeechRecognition);
    const hasMediaDevices = Boolean(navigator?.mediaDevices?.getUserMedia);
    setIsSupported(hasSpeechClass || hasMediaDevices);
  }, []);

  // Helper to commit and submit final transcript
  const commitAndSubmitTranscript = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    const textToSubmit = (latestTranscriptRef.current || '').trim();
    if (textToSubmit && !hasSubmittedRef.current) {
      hasSubmittedRef.current = true;
      setTranscript(textToSubmit);
      setInterimTranscript('');
      onFinalResultRef.current?.(textToSubmit);
    }
  }, []);

  const stopListening = useCallback(() => {
    isStoppingExplicitly.current = true;
    commitAndSubmitTranscript();

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }
    }
    setIsListening(false);
  }, [commitAndSubmitTranscript]);

  const startListening = useCallback(async () => {
    setError(null);
    setTranscript('');
    setInterimTranscript('');
    latestTranscriptRef.current = '';
    hasSubmittedRef.current = false;
    isStoppingExplicitly.current = false;

    // 1. Explicitly prompt / verify microphone permission
    if (navigator?.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Immediately release stream so SpeechRecognition can take audio device
        stream.getTracks().forEach((track) => track.stop());
      } catch (permErr: any) {
        if (
          permErr.name === 'NotAllowedError' ||
          permErr.name === 'PermissionDeniedError' ||
          permErr.message?.includes('denied')
        ) {
          const err = 'Microphone permission denied. Please allow microphone access in your browser.';
          setError(err);
          onErrorRef.current?.(err);
          setIsListening(false);
          return;
        }
      }
    }

    const win = typeof window !== 'undefined' ? (window as IWindow) : null;
    const SpeechRecognitionClass = win?.SpeechRecognition || win?.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      const err =
        'Speech recognition is not supported natively in this browser. Please use Chrome, Edge, or Safari, or type your message.';
      setError(err);
      onErrorRef.current?.(err);
      setIsListening(false);
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

      // Resolve language
      let targetLang = language;
      if (targetLang === 'auto') {
        targetLang = (navigator?.language as any) || 'en-US';
      }
      recognition.lang = targetLang;
      recognition.interimResults = true;
      recognition.continuous = true; // Stay listening until silence or user pause
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
          const text = result[0]?.transcript || '';

          if (result.isFinal) {
            final += text;
          } else {
            interim += text;
          }
        }

        if (final) {
          const trimmedFinal = final.trim();
          latestTranscriptRef.current = trimmedFinal;
          setTranscript(trimmedFinal);
          setInterimTranscript('');
          commitAndSubmitTranscript();
          return;
        }

        const currentPhrase = interim.trim();
        if (currentPhrase) {
          latestTranscriptRef.current = currentPhrase;
          setInterimTranscript(currentPhrase);

          // Reset silence debounce timer: 1.5 seconds of silence automatically commits and sends
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
          }
          silenceTimerRef.current = setTimeout(() => {
            if (!isStoppingExplicitly.current) {
              commitAndSubmitTranscript();
              try {
                recognition.stop();
              } catch {
                // ignore
              }
              setIsListening(false);
            }
          }, 1500);
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
            // No speech within recognition interval; if we have accumulated words, submit them
            if (latestTranscriptRef.current) {
              commitAndSubmitTranscript();
              setIsListening(false);
              return;
            }
            errorMessage = 'No speech detected. Please speak clearly into your microphone.';
            break;
          case 'network':
            errorMessage = 'Network error during speech recognition. Check your internet connection.';
            break;
          case 'aborted':
            return;
          default:
            errorMessage = `Voice recognition: ${event.error}`;
        }

        setError(errorMessage);
        onErrorRef.current?.(errorMessage);
        setIsListening(false);
      };

      recognition.onend = () => {
        if (!isStoppingExplicitly.current) {
          commitAndSubmitTranscript();
        }
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e: any) {
      const err = e?.message || 'Failed to start microphone.';
      setError(err);
      onErrorRef.current?.(err);
      setIsListening(false);
    }
  }, [language, commitAndSubmitTranscript]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
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
      latestTranscriptRef.current = '';
      hasSubmittedRef.current = false;
    },
  };
}
