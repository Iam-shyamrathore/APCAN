// WebSocket message types matching backend WSMessageType enum

export type WSMessageType =
  // Client → Server
  | "text_input"
  | "audio_chunk"
  | "session_start"
  | "session_end"
  | "ping"
  // Server → Client
  | "text_response"
  | "audio_response"
  | "tool_call"
  | "tool_result"
  | "error"
  | "session_created"
  | "pong"
  | "stream_start"
  | "stream_chunk"
  | "stream_end"
  | "agent_switch"
  | "agent_error"
  | "rate_limited";

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
  timestamp?: string;
  session_id?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  toolCalls?: ToolCallInfo[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ToolCallInfo {
  name: string;
  args?: Record<string, unknown>;
  success?: boolean;
  loading?: boolean;
}

export type AgentType = "intake" | "scheduling" | "care" | "admin" | "general";

export const AGENT_COLORS: Record<string, string> = {
  intake: "bg-blue-500/20 text-blue-400",
  scheduling: "bg-purple-500/20 text-purple-400",
  care: "bg-emerald-500/20 text-emerald-400",
  admin: "bg-amber-500/20 text-amber-400",
  general: "bg-slate-500/20 text-slate-400",
};

export const AGENT_LABELS: Record<string, string> = {
  intake: "Patient Intake",
  scheduling: "Scheduling",
  care: "Care Management",
  admin: "Administration",
  general: "General",
};
