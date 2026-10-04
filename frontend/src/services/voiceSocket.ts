/**
 * MR.GREEN — Real-Time Voice WebSocket Client
 *
 * Maintains persistent bidirectional WebSocket session for:
 * - Real-time streaming transcripts (STT)
 * - Immediate barge-in / interruption
 * - Streaming audio playback from CosyVoice
 * - Agent reasoning & tool execution states
 */

import { VoiceProfileId, VoiceState } from '../types/voice';

export interface VoiceSocketCallbacks {
  onStateChange: (state: VoiceState) => void;
  onPartialTranscript: (text: string) => void;
  onFinalTranscript: (text: string) => void;
  onResponseDelta: (delta: string) => void;
  onResponseDone: (data: { response: string; conversation_id: string; agent_run_id?: string }) => void;
  onAudioStart?: () => void;
  onAudioChunk?: (base64Audio: string) => void;
  onAudioEnd?: () => void;
  onInterrupted: () => void;
  onError: (errorMsg: string) => void;
}

export class VoiceSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: VoiceSocketCallbacks;
  private isExplicitlyClosed: boolean = false;
  private reconnectTimer: any = null;
  private audioQueue: string[] = [];
  private isPlayingAudio: boolean = false;
  private currentAudioElement: HTMLAudioElement | null = null;

  constructor(callbacks: VoiceSocketCallbacks) {
    this.callbacks = callbacks;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/api/voice/ws`;
  }

  public connect(conversationId?: string, profile?: VoiceProfileId, language?: string): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    this.callbacks.onStateChange('CONNECTING');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
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
          console.error('[VoiceWS] Failed to parse event JSON:', e);
        }
      };

      this.ws.onerror = () => {
        this.callbacks.onStateChange('ERROR');
      };

      this.ws.onclose = () => {
        if (!this.isExplicitlyClosed) {
          this.callbacks.onStateChange('DISCONNECTED');
          this.scheduleReconnect(conversationId, profile, language);
        }
      };
    } catch {
      this.callbacks.onStateChange('ERROR');
    }
  }

  private scheduleReconnect(conversationId?: string, profile?: VoiceProfileId, language?: string): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      if (!this.isExplicitlyClosed) {
        this.connect(conversationId, profile, language);
      }
    }, 4000);
  }

  private handleServerEvent(data: any): void {
    const type = data.type;

    switch (type) {
      case 'voice.state':
        if (data.state) {
          this.callbacks.onStateChange(data.state as VoiceState);
        }
        break;

      case 'transcript.partial':
        if (data.text) this.callbacks.onPartialTranscript(data.text);
        break;

      case 'transcript.final':
        if (data.text) this.callbacks.onFinalTranscript(data.text);
        break;

      case 'response.text.delta':
        if (data.delta) this.callbacks.onResponseDelta(data.delta);
        break;

      case 'response.text.done':
        this.callbacks.onResponseDone({
          response: data.response || '',
          conversation_id: data.conversation_id || '',
          agent_run_id: data.agent_run_id,
        });
        break;

      case 'audio.start':
        this.callbacks.onAudioStart?.();
        break;

      case 'audio.chunk':
        if (data.audio_data) {
          this.enqueueAudioChunk(data.audio_data);
          this.callbacks.onAudioChunk?.(data.audio_data);
        }
        break;

      case 'audio.end':
        this.callbacks.onAudioEnd?.();
        break;

      case 'assistant.interrupted':
        this.stopAudioPlayback();
        this.callbacks.onInterrupted();
        break;

      case 'error':
        this.callbacks.onError(data.error || 'Voice error occurred.');
        break;
    }
  }

  public sendTranscript(text: string, isFinal: boolean = true): void {
    this.sendEvent('transcript.input', { text, is_final: isFinal });
  }

  public interrupt(): void {
    this.stopAudioPlayback();
    this.sendEvent('user.interrupt', {});
  }

  public sendEvent(type: string, payload: Record<string, any>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  private enqueueAudioChunk(base64Wav: string): void {
    this.audioQueue.push(base64Wav);
    if (!this.isPlayingAudio) {
      this.playNextAudioChunk();
    }
  }

  private playNextAudioChunk(): void {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      return;
    }

    this.isPlayingAudio = true;
    const chunk = this.audioQueue.shift();
    if (!chunk) {
      this.playNextAudioChunk();
      return;
    }

    try {
      const audioUrl = `data:audio/wav;base64,${chunk}`;
      const audio = new Audio(audioUrl);
      this.currentAudioElement = audio;

      audio.onended = () => {
        this.currentAudioElement = null;
        this.playNextAudioChunk();
      };

      audio.onerror = () => {
        this.currentAudioElement = null;
        this.playNextAudioChunk();
      };

      audio.play().catch(() => {
        // Autoplay may be restricted by browser until user gesture
        this.playNextAudioChunk();
      });
    } catch {
      this.playNextAudioChunk();
    }
  }

  public stopAudioPlayback(): void {
    this.audioQueue = [];
    this.isPlayingAudio = false;
    if (this.currentAudioElement) {
      try {
        this.currentAudioElement.pause();
        this.currentAudioElement.currentTime = 0;
      } catch {
        // Ignore
      }
      this.currentAudioElement = null;
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.stopAudioPlayback();
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      try {
        this.sendEvent('session.stop', {});
        this.ws.close();
      } catch {
        // Ignore
      }
      this.ws = null;
    }
    this.callbacks.onStateChange('DISCONNECTED');
  }
}
