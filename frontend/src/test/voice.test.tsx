import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';

describe('Voice Input — useSpeechRecognition', () => {
  let originalSpeechRecognition: any;
  let originalWebkitSpeechRecognition: any;

  beforeEach(() => {
    originalSpeechRecognition = (window as any).SpeechRecognition;
    originalWebkitSpeechRecognition = (window as any).webkitSpeechRecognition;
  });

  afterEach(() => {
    (window as any).SpeechRecognition = originalSpeechRecognition;
    (window as any).webkitSpeechRecognition = originalWebkitSpeechRecognition;
    vi.restoreAllMocks();
  });

  it('detects when browser does not support recognition', () => {
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.isSupported).toBe(false);
  });

  it('detects when browser supports recognition', () => {
    (window as any).SpeechRecognition = function () {
      this.start = vi.fn();
      this.stop = vi.fn();
      this.abort = vi.fn();
    };

    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.isSupported).toBe(true);
  });

  it('handles microphone recognition start and end events', () => {
    let instance: any;
    (window as any).SpeechRecognition = function () {
      instance = this;
      this.start = vi.fn();
      this.stop = vi.fn();
      this.abort = vi.fn();
      this.onstart = null;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
    };

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
    });

    // Simulate onstart
    act(() => {
      instance.onstart();
    });
    expect(result.current.isListening).toBe(true);

    // Simulate onend
    act(() => {
      instance.onend();
    });
    expect(result.current.isListening).toBe(false);
  });

  it('handles microphone recognition result and interim transcript', () => {
    let instance: any;
    const onFinalResult = vi.fn();

    (window as any).SpeechRecognition = function () {
      instance = this;
      this.start = vi.fn();
      this.stop = vi.fn();
      this.abort = vi.fn();
      this.onstart = null;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
    };

    const { result } = renderHook(() =>
      useSpeechRecognition({ onFinalResult, language: 'en-IN' })
    );

    act(() => {
      result.current.startListening();
    });

    // Simulate interim result
    act(() => {
      instance.onresult({
        resultIndex: 0,
        results: [
          [{ transcript: 'Hello MR' }],
        ],
      });
    });
    expect(result.current.interimTranscript).toBe('Hello MR');

    // Simulate final result
    const finalEvent = {
      resultIndex: 0,
      results: [
        Object.assign([{ transcript: 'Hello MR.GREEN' }], { isFinal: true }),
      ],
    };
    act(() => {
      instance.onresult(finalEvent);
    });
    expect(onFinalResult).toHaveBeenCalledWith('Hello MR.GREEN');
  });

  it('handles microphone permission denied error', () => {
    let instance: any;
    const onError = vi.fn();

    (window as any).SpeechRecognition = function () {
      instance = this;
      this.start = vi.fn();
      this.stop = vi.fn();
      this.abort = vi.fn();
      this.onstart = null;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
    };

    const { result } = renderHook(() => useSpeechRecognition({ onError }));

    act(() => {
      result.current.startListening();
    });

    act(() => {
      instance.onerror({ error: 'not-allowed' });
    });

    expect(result.current.error).toContain('Microphone permission denied');
    expect(onError).toHaveBeenCalled();
  });

  it('handles general speech recognition errors', () => {
    let instance: any;
    const onError = vi.fn();

    (window as any).SpeechRecognition = function () {
      instance = this;
      this.start = vi.fn();
      this.stop = vi.fn();
      this.abort = vi.fn();
      this.onstart = null;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
    };

    const { result } = renderHook(() => useSpeechRecognition({ onError }));

    act(() => {
      result.current.startListening();
    });

    act(() => {
      instance.onerror({ error: 'network' });
    });

    expect(result.current.error).toContain('Network error');
    expect(onError).toHaveBeenCalled();
  });
});

describe('Text-To-Speech — useSpeechSynthesis', () => {
  let originalSpeechSynthesis: any;
  let mockSpeak: any;
  let mockCancel: any;
  let mockPause: any;
  let mockResume: any;
  let lastUtteranceInstance: any;

  beforeEach(() => {
    originalSpeechSynthesis = window.speechSynthesis;

    mockSpeak = vi.fn();
    mockCancel = vi.fn();
    mockPause = vi.fn();
    mockResume = vi.fn();

    const mockVoices = [
      { name: 'Google UK English Female', lang: 'en-GB', voiceURI: 'en-gb-1' },
      { name: 'Google Indian English', lang: 'en-IN', voiceURI: 'en-in-1' },
    ];

    Object.defineProperty(window, 'speechSynthesis', {
      writable: true,
      value: {
        getVoices: vi.fn().mockReturnValue(mockVoices),
        speak: mockSpeak,
        cancel: mockCancel,
        pause: mockPause,
        resume: mockResume,
        onvoiceschanged: null,
      },
    });

    (window as any).SpeechSynthesisUtterance = function (text: string) {
      this.text = text;
      this.lang = 'en-IN';
      this.rate = 1.0;
      this.pitch = 1.0;
      this.voice = null;
      this.onstart = null;
      this.onend = null;
      this.onerror = null;
      lastUtteranceInstance = this;
    };
  });

  afterEach(() => {
    Object.defineProperty(window, 'speechSynthesis', {
      writable: true,
      value: originalSpeechSynthesis,
    });
    vi.restoreAllMocks();
  });

  it('detects when speech synthesis is available and loads voice list', () => {
    const { result } = renderHook(() => useSpeechSynthesis());
    expect(result.current.isSupported).toBe(true);
    expect(result.current.voices.length).toBe(2);
  });

  it('speaks text when requested and cleans technical markdown', () => {
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => {
      result.current.speak('```python\nprint(1)\n``` Hello **MR.GREEN**! Here is `code`');
    });

    expect(mockSpeak).toHaveBeenCalled();
    const utteranceArg = mockSpeak.mock.calls[0][0];
    expect(utteranceArg.text).toContain('Hello MR.GREEN!');
    expect(utteranceArg.text).not.toContain('```');
    expect(utteranceArg.text).not.toContain('**');
  });

  it('stops speech when requested', () => {
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => {
      result.current.stop();
    });

    expect(mockCancel).toHaveBeenCalled();
    expect(result.current.isSpeaking).toBe(false);
  });

  it('pauses and resumes speech', () => {
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => {
      result.current.speak('Testing speech');
    });

    // Simulate speaking state
    act(() => {
      lastUtteranceInstance.onstart();
    });
    expect(result.current.isSpeaking).toBe(true);

    act(() => {
      result.current.pause();
    });
    expect(mockPause).toHaveBeenCalled();
    expect(result.current.isPaused).toBe(true);

    act(() => {
      result.current.resume();
    });
    expect(mockResume).toHaveBeenCalled();
    expect(result.current.isPaused).toBe(false);
  });

  it('handles speech synthesis error gracefully', () => {
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => {
      result.current.speak('Error test');
    });

    act(() => {
      lastUtteranceInstance.onerror({ error: 'audio-busy' });
    });

    expect(result.current.isSpeaking).toBe(false);
  });
});
