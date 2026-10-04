export type MessageRole = 'user' | 'assistant' | 'system';

export interface ToolActivity {
  id: string;
  toolName: string;
  actionType?: string;
  success?: boolean;
  durationMs?: number;
  summary?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  status?: 'sending' | 'sent' | 'error';
  agentRunId?: string;
  toolActivities?: ToolActivity[];
  durationMs?: number;
}

export interface ChatRequestPayload {
  message: string;
  conversation_id?: string;
}

export interface ChatResponsePayload {
  response: string;
  conversation_id: string;
  message_id: string;
  extracted_memories?: Array<{
    type: string;
    key: string;
    content: string;
  }>;
  agent_run_id?: string | null;
  iterations?: number;
  duration_ms?: number;
}
