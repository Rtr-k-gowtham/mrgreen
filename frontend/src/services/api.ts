import {
  ChatRequestPayload,
  ChatResponsePayload,
} from '../types/chat';
import {
  ConversationSummary,
  ConversationDetail,
  AgentRunDetail,
  HealthResponse,
  ToolInfo,
} from '../types/agent';

const getApiBaseUrl = () => {
  const envUrl = import.meta.env?.VITE_API_BASE_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null') {
    return window.location.origin;
  }
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

class ApiClient {
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
  }

  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: this.getHeaders(),
        // Timeout after 5s to avoid freezing mobile UI
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        return { status: 'unhealthy' };
      }

      return await response.json();
    } catch {
      return { status: 'offline' };
    }
  }

  async sendChatMessage(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorDetail = 'Failed to get response from MR.GREEN.';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorDetail = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : JSON.stringify(errorData.detail);
          }
        } catch {
          // ignore parsing error
        }
        throw new Error(errorDetail);
      }

      return await response.json();
    } catch (err: unknown) {
      if (err instanceof Error) {
        // Strip out any sensitive stack traces
        const cleanMessage = err.message.replace(/(\r\n|\n|\r)/gm, ' ').substring(0, 200);
        throw new Error(cleanMessage);
      }
      throw new Error('Connection to MR.GREEN failed. Please check your network.');
    }
  }

  async getConversations(limit = 30): Promise<ConversationSummary[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations?limit=${limit}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to load conversations.');
      }

      return await response.json();
    } catch (err) {
      console.warn('Error fetching conversations:', err);
      return [];
    }
  }

  async getConversation(id: string): Promise<ConversationDetail | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${id}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Conversation ${id} not found.`);
      }

      return await response.json();
    } catch (err) {
      console.warn('Error fetching conversation detail:', err);
      return null;
    }
  }

  async getAgentRun(runId: string): Promise<AgentRunDetail | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/runs/${runId}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch {
      return null;
    }
  }

  async listTools(): Promise<ToolInfo[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch {
      return [];
    }
  }
}

export const api = new ApiClient();
