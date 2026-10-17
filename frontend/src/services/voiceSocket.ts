/**
 * MR.GREEN — Real-Time Voice WebSocket Client
 *
 * Maintains persistent bidirectional WebSocket session for:
 * - Real-time streaming transcripts (STT)
 * - Immediate barge-in / interruption
 * - Streaming audio playback from CosyVoice (accumulated into complete WAV blobs)
 * - Agent reasoning & tool execution states
 */

import { VoiceProfileId, VoiceState } from '../types/voice';

/** Diagnostic event for debug panel and structured logging. */
export interface VoiceDiagnosticEvent {
  timestamp: number;
  stage: string;
  detail: string;
  level: 'info' | 'warn' | 'error';
}

export interface VoiceSocketCallbacks {
  onStateChange: (state: VoiceState) => void;
  onPartialTranscript: (text: string) => void;
  onFinalTranscript: (text: string) => void;
  onResponseDelta: (delta: string) => void;
  onResponseDone: (data: {
    response: string;
    conversation_id: string;
    agent_run_id?: string;
    iterations?: number;
  }) => void;
  onAudioStart?: () => void;
  onAudioChunk?: (base64Audio: string) => void;
  onAudioEnd?: () => void;
  onAudioPlaybackStarted?: () => void;
  onAudioPlaybackEnded?: () => void;
  onInterrupted: () => void;
  onError: (errorMsg: string) => void;
  onDiagnostic?: (event: VoiceDiagnosticEvent) => void;
}

export class VoiceSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: VoiceSocketCallbacks;
  private isExplicitlyClosed: boolean = false;
  private reconnectTimer: any = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private connectionTimeout: any = null;

  // Audio accumulation — collect chunks between audio.start / audio.end
  private audioChunkBuffer: Uint8Array[] = [];
  private audioPlaybackQueue: Blob[] = [];
  private currentAudioFormat: string = 'mp3';
  private isPlayingAudio: boolean = false;
  private currentAudioElement: HTMLAudioElement | null = null;
  private currentAudioUrl: string | null = null;

  // Server capability flags
  private _ttsAvailable: boolean = false;

  // Reconnection parameters stored for auto-reconnect
  private _lastConversationId?: string;
  private _lastProfile?: VoiceProfileId;
  private _lastLanguage?: string;

  constructor(callbacks: VoiceSocketCallbacks) {
    this.callbacks = callbacks;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/api/voice/ws`;
  }

  /** True if the WebSocket is open and ready. */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /** True if the backend reports TTS is available and operational. */
  public isTtsAvailable(): boolean {
    return this._ttsAvailable;
  }

  /**
   * Unlock browser HTML5 Audio playback via user gesture.
   */
  public unlockAudio(): void {
    try {
      if (typeof window !== 'undefined') {
        const silentAudio = new Audio(
          'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA',
        );
        silentAudio.volume = 0.01;
        const p = silentAudio.play();
        if (p !== undefined) {
          p.then(() => {
            silentAudio.pause();
          }).catch(() => {});
        }
      }
    } catch {
      // Ignore
    }
  }

  public connect(
    conversationId?: string,
    profile?: VoiceProfileId,
    language?: string,
  ): void {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this._lastConversationId = conversationId;
    this._lastProfile = profile;
    this._lastLanguage = language;
    this.isExplicitlyClosed = false;
    this.emitDiagnostic('VOICE_WS_CONNECTING', `Connecting to ${this.url}`);
    this.callbacks.onStateChange('CONNECTING');

    // Connection timeout (10 s)
    this.connectionTimeout = setTimeout(() => {
      if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
        this.emitDiagnostic(
          'VOICE_WS_ERROR',
          'Connection timeout after 10 s',
          'error',
        );
        this.ws.close();
      }
    }, 10_000);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
        this.reconnectAttempts = 0;
        this.emitDiagnostic('VOICE_WS_CONNECTED', 'WebSocket connected');
        this.callbacks.onStateChange('CONNECTED');
        this.sendEvent('session.start', {
          conversation_id: conversationId,
          voice_profile: profile || 'GREEN_DEFAULT',
          language: language || 'auto',
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleServerEvent(data);
        } catch (e) {
          this.emitDiagnostic(
            'VOICE_WS_ERROR',
            `Failed to parse event: ${e}`,
            'error',
          );
        }
      };

      this.ws.onerror = () => {
        if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
        this.emitDiagnostic('VOICE_WS_ERROR', 'WebSocket error', 'error');
        this.callbacks.onStateChange('ERROR');
      };

      this.ws.onclose = (event) => {
        if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
        this.emitDiagnostic(
          'VOICE_WS_DISCONNECTED',
          `Code: ${event.code}, Reason: ${event.reason || 'none'}`,
        );
        if (!this.isExplicitlyClosed) {
          this.callbacks.onStateChange('DISCONNECTED');
          this.scheduleReconnect();
        }
      };
    } catch (e) {
      if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
      this.emitDiagnostic(
        'VOICE_WS_ERROR',
        `Failed to create WebSocket: ${e}`,
        'error',
      );
      this.callbacks.onStateChange('ERROR');
    }
  }

  /**
   * Update session parameters without disconnecting / reconnecting.
   * Sends a session.start event over the existing WebSocket.
   */
  public updateSession(
    conversationId?: string | null,
    profile?: VoiceProfileId,
    language?: string,
  ): void {
    if (!this.isConnected()) return;
    const payload: Record<string, any> = {};
    if (conversationId) payload.conversation_id = conversationId;
    if (profile) payload.voice_profile = profile;
    if (language) payload.language = language;
    if (Object.keys(payload).length === 0) return;
    this.sendEvent('session.start', payload);
    this.emitDiagnostic(
      'VOICE_WS_CONNECTED',
      `Session updated: conv=${conversationId ?? '—'} profile=${profile ?? '—'}`,
    );
  }

  // ── Reconnection with exponential backoff ──────────────────────────

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emitDiagnostic(
        'VOICE_WS_ERROR',
        `Max reconnect attempts (${this.maxReconnectAttempts}) reached`,
        'error',
      );
      this.callbacks.onError(
        'Voice connection lost. Please refresh or check your network.',
      );
      return;
    }
    const delay = Math.min(
      2000 * Math.pow(1.5, this.reconnectAttempts),
      15_000,
    );
    this.reconnectAttempts++;
    this.emitDiagnostic(
      'VOICE_WS_CONNECTING',
      `Reconnecting in ${Math.round(delay)} ms (attempt ${this.reconnectAttempts})`,
    );
    this.reconnectTimer = setTimeout(() => {
      if (!this.isExplicitlyClosed) {
        this.connect(
          this._lastConversationId,
          this._lastProfile as VoiceProfileId | undefined,
          this._lastLanguage,
        );
      }
    }, delay);
  }

  // ── Server event handler ──────────────────────────────────────────

  private handleServerEvent(data: any): void {
    const type = data.type;

    switch (type) {
      case 'session.ready':
        this._ttsAvailable = data.tts_available === true;
        this.emitDiagnostic(
          'VOICE_WS_CONNECTED',
          `Session ready | conv=${data.conversation_id ?? '—'} | tts=${this._ttsAvailable}`,
        );
        break;

      case 'voice.state':
        if (data.state) {
          this.callbacks.onStateChange(data.state as VoiceState);
        }
        break;

      case 'transcript.partial':
        if (data.text) {
          this.emitDiagnostic('STT_PARTIAL', data.text);
          this.callbacks.onPartialTranscript(data.text);
        }
        break;

      case 'transcript.final':
        if (data.text) {
          this.emitDiagnostic('STT_FINAL', data.text);
          this.callbacks.onFinalTranscript(data.text);
        }
        break;

      case 'agent.thinking':
        this.emitDiagnostic(
          'AGENT_STARTED',
          `Processing: "${(data.message || '').substring(0, 60)}"`,
        );
        break;

      case 'response.text.delta':
        if (data.delta) this.callbacks.onResponseDelta(data.delta);
        break;

      case 'response.text.done':
        this.emitDiagnostic(
          'LLM_COMPLETED',
          `Response length: ${(data.response || '').length}`,
        );
        this.callbacks.onResponseDone({
          response: data.response || '',
          conversation_id: data.conversation_id || '',
          agent_run_id: data.agent_run_id,
          iterations: data.iterations,
        });
        break;

      case 'audio.start':
        this.audioChunkBuffer = [];
        this.currentAudioFormat = (data.format || 'mp3').toLowerCase();
        this.emitDiagnostic(
          'TTS_STARTED',
          `Sentence: "${(data.text || '').substring(0, 60)}" (Format: ${this.currentAudioFormat})`,
        );
        this.callbacks.onAudioStart?.();
        break;

      case 'audio.chunk':
        if (data.audio_data) {
          this.accumulateAudioChunk(data.audio_data);
          this.callbacks.onAudioChunk?.(data.audio_data);
        }
        break;

      case 'audio.end':
        this.finalizeAndQueueAudio();
        this.emitDiagnostic('TTS_COMPLETED', 'Queued audio for playback');
        this.callbacks.onAudioEnd?.();
        break;

      case 'assistant.interrupted':
        this.stopAudioPlayback();
        this.emitDiagnostic('VOICE_INTERRUPTED', 'Assistant speech interrupted');
        this.callbacks.onInterrupted();
        break;

      case 'error':
        this.emitDiagnostic(
          'VOICE_PIPELINE_ERROR',
          data.error || 'Unknown error',
          'error',
        );
        this.callbacks.onError(data.error || 'Voice error occurred.');
        break;

      case 'pong':
        // keepalive response — no action required
        break;
    }
  }

  // ── Audio chunk accumulation and playback ─────────────────────────

  private accumulateAudioChunk(base64Data: string): void {
    try {
      const binaryStr = atob(base64Data);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      this.audioChunkBuffer.push(bytes);
    } catch (e) {
      this.emitDiagnostic(
        'VOICE_PIPELINE_ERROR',
        `Failed to decode audio chunk: ${e}`,
        'error',
      );
    }
  }

  /**
   * Combine all accumulated chunks for one sentence into a single WAV Blob
   * and enqueue it for sequential playback.
   */
  private finalizeAndQueueAudio(): void {
    if (this.audioChunkBuffer.length === 0) return;

    const totalLength = this.audioChunkBuffer.reduce(
      (acc, c) => acc + c.length,
      0,
    );
    const combined = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of this.audioChunkBuffer) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }
    this.audioChunkBuffer = [];

    const mimeType = this.currentAudioFormat === 'mp3' ? 'audio/mpeg' : 'audio/wav';
    const blob = new Blob([combined], { type: mimeType });
    this.audioPlaybackQueue.push(blob);

    if (!this.isPlayingAudio) {
      this.playNextFromQueue();
    }
  }

  private playNextFromQueue(): void {
    if (this.audioPlaybackQueue.length === 0) {
      this.isPlayingAudio = false;
      this.callbacks.onAudioPlaybackEnded?.();
      return;
    }

    this.isPlayingAudio = true;
    const blob = this.audioPlaybackQueue.shift()!;

    // Revoke previous Object URL to avoid memory leaks
    if (this.currentAudioUrl) {
      URL.revokeObjectURL(this.currentAudioUrl);
      this.currentAudioUrl = null;
    }

    try {
      const url = URL.createObjectURL(blob);
      this.currentAudioUrl = url;
      const audio = new Audio(url);
      this.currentAudioElement = audio;

      audio.onplay = () => {
        this.emitDiagnostic('AUDIO_PLAYBACK_STARTED', 'Playing audio segment');
        this.callbacks.onAudioPlaybackStarted?.();
      };

      audio.onended = () => {
        this.cleanupCurrentAudio();
        this.playNextFromQueue();
      };

      audio.onerror = () => {
        this.emitDiagnostic(
          'AUDIO_PLAYBACK_BLOCKED',
          'Audio element error — skipping segment',
          'warn',
        );
        this.cleanupCurrentAudio();
        this.playNextFromQueue();
      };

      audio.play().catch((err) => {
        this.emitDiagnostic(
          'AUDIO_PLAYBACK_BLOCKED',
          `Autoplay blocked: ${err.message}`,
          'warn',
        );
        this.cleanupCurrentAudio();
        this.playNextFromQueue();
      });
    } catch (e) {
      this.emitDiagnostic(
        'AUDIO_PLAYBACK_BLOCKED',
        `Failed to create audio element: ${e}`,
        'error',
      );
      this.playNextFromQueue();
    }
  }

  private cleanupCurrentAudio(): void {
    this.currentAudioElement = null;
    if (this.currentAudioUrl) {
      URL.revokeObjectURL(this.currentAudioUrl);
      this.currentAudioUrl = null;
    }
  }

  // ── Public API ────────────────────────────────────────────────────

  public sendTranscript(text: string, isFinal: boolean = true): void {
    this.emitDiagnostic(
      isFinal ? 'STT_FINAL' : 'STT_PARTIAL',
      `Sending transcript: "${text.substring(0, 60)}"`,
    );
    this.sendEvent('transcript.input', { text, is_final: isFinal });
  }

  public interrupt(): void {
    this.stopAudioPlayback();
    this.sendEvent('user.interrupt', {});
    this.emitDiagnostic('VOICE_INTERRUPTED', 'User-initiated interrupt');
  }

  public sendEvent(type: string, payload: Record<string, any>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  public stopAudioPlayback(): void {
    this.audioPlaybackQueue = [];
    this.audioChunkBuffer = [];
    this.isPlayingAudio = false;
    if (this.currentAudioElement) {
      try {
        this.currentAudioElement.pause();
        this.currentAudioElement.currentTime = 0;
      } catch {
        // ignore
      }
      this.currentAudioElement = null;
    }
    if (this.currentAudioUrl) {
      URL.revokeObjectURL(this.currentAudioUrl);
      this.currentAudioUrl = null;
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.stopAudioPlayback();
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
    if (this.ws) {
      try {
        this.sendEvent('session.stop', {});
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this.callbacks.onStateChange('DISCONNECTED');
  }

  // ── Diagnostic logging ────────────────────────────────────────────

  private emitDiagnostic(
    stage: string,
    detail: string,
    level: 'info' | 'warn' | 'error' = 'info',
  ): void {
    const event: VoiceDiagnosticEvent = {
      timestamp: Date.now(),
      stage,
      detail,
      level,
    };

    const prefix = `[MR.GREEN Voice] [${stage}]`;
    if (level === 'error') console.error(prefix, detail);
    else if (level === 'warn') console.warn(prefix, detail);
    else console.log(prefix, detail);

    this.callbacks.onDiagnostic?.(event);
  }
}
