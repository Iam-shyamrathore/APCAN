// API response types matching backend Pydantic schemas

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: "admin" | "clinician" | "patient" | "agent";
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Patient {
  id: number;
  user_id: number;
  mrn: string | null;
  given_name: string;
  family_name: string;
  birth_date: string;
  gender: string | null;
  phone: string | null;
  address_line: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  created_at: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  status:
    | "proposed"
    | "pending"
    | "booked"
    | "arrived"
    | "fulfilled"
    | "cancelled"
    | "noshow";
  appointment_type: string | null;
  description: string | null;
  start_time: string;
  end_time: string;
  provider_name: string | null;
  location: string | null;
  notes: string | null;
  created_at: string;
}

export interface Encounter {
  id: number;
  patient_id: number;
  status: string;
  encounter_type: string | null;
  reason: string | null;
  start_time: string;
  end_time: string | null;
  provider_name: string | null;
  notes: string | null;
  created_at: string;
}

export interface Observation {
  id: number;
  patient_id: number;
  encounter_id: number | null;
  code: string;
  display: string | null;
  category: string | null;
  value: string | null;
  unit: string | null;
  status: string;
  effective_date: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user_id: number | null;
  session_id: string | null;
  agent: string | null;
  action: string;
  tool_name: string | null;
  tool_args: Record<string, unknown> | null;
  patient_id: number | null;
  resource_type: string | null;
  resource_id: string | null;
  success: boolean;
  error_message: string | null;
}

export interface ConversationSession {
  session_id: string;
  status: string;
  patient_id: number | null;
  started_at: string;
  ended_at: string | null;
  message_count: number;
}

export interface ConversationMessage {
  id: number;
  role: "user" | "assistant" | "tool";
  content: string;
  tool_calls: Record<string, unknown> | null;
  tool_results: Record<string, unknown> | null;
  tokens_used: number | null;
  latency_ms: number | null;
  created_at: string;
}
