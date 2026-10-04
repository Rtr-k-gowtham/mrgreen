export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  messages: ConversationMessage[];
}

export interface AgentStep {
  id: string;
  step_number: number;
  action_type: string;
  tool_name: string | null;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  success: boolean | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface AgentRunDetail {
  id: string;
  conversation_id: string;
  status: string;
  goal: string | null;
  current_step: number;
  total_steps: number;
  iterations: number;
  max_iterations: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  steps: AgentStep[];
}

export interface HealthResponse {
  status: string;
  service?: string;
  components?: {
    api?: { status: string };
    ai?: {
      status: string;
      provider?: string;
      model?: string;
      model_available?: boolean;
    };
  };
}

export interface ToolInfo {
  name: string;
  description: string;
  category?: string;
  risk_level?: string;
  requires_approval?: boolean;
  enabled?: boolean;
}
