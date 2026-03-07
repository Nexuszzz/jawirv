/* ========================================
   JAWIR OS — TypeScript Type Definitions
   ======================================== */

// ===== Agent Status Types =====
export type AgentStatus =
  | 'idle'
  | 'thinking'
  | 'planning'
  | 'executing_tool'
  | 'tool_completed'
  | 'tool_error'
  | 'observation'
  | 'searching'
  | 'reading'
  | 'writing'
  | 'iteration_start'
  | 'done'
  | 'error'
  | 'disconnected';

// ===== WebSocket Message Types =====
export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export interface WSUserMessage {
  type: 'user_message';
  data: {
    content: string;
    session_id: string;
  };
}

export interface WSUserMessageWithFile {
  type: 'user_message_with_file';
  data: {
    content: string;
    session_id: string;
    file_path: string;
    file_type: string;
  };
}

// ===== Chat Types =====
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  file?: {
    name: string;
    path: string;
    type: string;
  };
}

// ===== ReAct Step Types =====
export interface ReActStep {
  type: AgentStatus;
  message?: string;
  content?: string;
  toolName?: string;
  result?: unknown;
  duration?: number;
  details?: Record<string, unknown>;
  timestamp: number;
}

export interface ReActIteration {
  number: number;
  maxIterations: number;
  steps: ReActStep[];
  timestamp: number;
}

// ===== Tool Types =====
export interface ToolResult {
  id: string;
  toolName: string;
  status: string;
  title?: string;
  summary?: string;
  data?: Record<string, unknown>;
  timestamp: number;
  duration?: number;
}

export interface ToolCategory {
  id: string;
  name: string;
  icon: string;
  color: string;
  tools: ToolInfo[];
}

// ===== Health Status =====
export interface HealthStatus {
  status: string;
  version?: string;
  timestamp?: number;
  agent_model?: string;
  tools_count?: number;
  checks?: Record<string, boolean>;
}

export interface ToolInfo {
  name: string;
  description: string;
  icon: string;
}

// ===== Upload Types =====
export interface UploadedFile {
  filename: string;
  original_name: string;
  file_type: string;
  size: number;
  path: string;
  url: string;
}

// ===== UI Types =====
export type TabId = 'chat' | 'react' | 'tools' | 'dashboard' | 'iot';

export interface Tab {
  id: TabId;
  label: string;
  icon: string;
}

// ===== Tool Analytics =====
export interface ToolAnalytics {
  tool_name: string;
  call_count: number;
  success_count: number;
  error_count: number;
  avg_duration_ms: number;
}

// ===== Voice Types =====
export type VoiceMode =
  | 'idle'           // Not listening
  | 'wake_listening' // Listening for "Hey Jawir"
  | 'recording'      // Actively recording speech
  | 'processing'     // Processing transcript
  | 'error';         // Error state

export interface VoiceState {
  mode: VoiceMode;
  isEnabled: boolean;
  isWakeWordEnabled: boolean;
  interimTranscript: string;
  finalTranscript: string;
  error: string | null;
  audioLevel: number; // 0-1 for visualization
  language: 'id' | 'en' | 'multi';
}

export interface VoiceConfig {
  deepgramApiKey: string;
  language: 'id' | 'en' | 'multi';
  wakeWordEnabled: boolean;
  pushToTalkKey: string; // keyboard shortcut
  autoSubmit: boolean; // auto submit after silence
  endpointingMs: number; // silence threshold
}

export interface DeepgramTranscript {
  channel: {
    alternatives: Array<{
      transcript: string;
      confidence: number;
      words?: Array<{
        word: string;
        start: number;
        end: number;
        confidence: number;
      }>;
    }>;
  };
  is_final: boolean;
  speech_final: boolean;
  from_finalize?: boolean;
}
