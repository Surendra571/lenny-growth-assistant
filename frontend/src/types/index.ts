export interface SourceCitation {
  chunk_id?: string;
  episode_title: string;
  guest_name: string;
  timestamp?: string;
  relevance_score: number;
  snippet: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  metadata?: {
    intent?: string;
    skill?: string;
    title?: string;
    word_count?: number;
    artifact_id?: string;
    sources?: SourceCitation[];
    model?: string;
    [key: string]: any;
  };
  created_at: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  title: string;
  artifact_type: 'markdown' | 'html' | 'svg';
  content: string;
  version: number;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  llm_provider: string;
  active_model?: string;
  database_connected?: boolean;
}

export interface ChatResponse {
  session_id: string;
  intent: 'qa' | 'ship30';
  user_message: Message;
  assistant_message: Message;
  sources: SourceCitation[];
}

export interface Ship30Response {
  session_id: string;
  title: string;
  content: string;
  word_count: number;
  sources: SourceCitation[];
  metadata?: Record<string, any>;
  user_message?: Message;
  assistant_message?: Message;
}
