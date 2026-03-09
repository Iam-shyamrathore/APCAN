# Voice AI Integration Guide

## Overview

Phase 3 adds real-time voice/text AI interaction powered by Google Gemini 2.0 Flash. The AI assistant can query patient records, book appointments, and retrieve clinical data through natural language.

## Architecture

```
Client (WebSocket) → Voice Router → Gemini Service → AI FHIR Service → Database
                                  ↕
                         Conversation Manager
```

## WebSocket Endpoint

### `WS /api/v1/voice/ws?token={jwt_token}`

Establishes a real-time AI conversation session.

**Authentication**: JWT token passed as query parameter.

**Message Flow**:
1. Client connects with JWT token
2. Server creates conversation session
3. Client sends `text_input` messages
4. Server responds with `text_response` (optionally `stream_chunk` for streaming)
5. If Gemini invokes FHIR tools, server executes them and feeds results back to Gemini
6. Client sends `session_end` to close

**Message Types** (client → server):
```json
{"type": "text_input", "text": "Show me John's appointments"}
{"type": "session_end"}
```

**Message Types** (server → client):
```json
{"type": "session_start", "session_id": "uuid"}
{"type": "text_response", "text": "John has 2 upcoming appointments..."}
{"type": "tool_call", "tool_name": "get_patient_appointments", "args": {...}}
{"type": "tool_result", "tool_name": "...", "result": {...}}
{"type": "error", "message": "..."}
{"type": "session_ended"}
```

## REST Endpoints

### `GET /api/v1/voice/sessions/{session_id}`

Retrieve conversation history for a session.

**Response**:
```json
{
  "session_id": "uuid",
  "status": "active",
  "messages": [
    {"role": "user", "content": "...", "created_at": "..."},
    {"role": "assistant", "content": "...", "tool_calls": [...]}
  ],
  "started_at": "...",
  "message_count": 5
}
```

### `POST /api/v1/voice/sessions/{session_id}/end`

End an active conversation session.

## AI Tool Calling

The Gemini model has access to 7 FHIR tools:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_patients` | `query` (str) | Search patients by name or MRN |
| `get_patient` | `patient_id` (int) | Get patient demographics |
| `get_patient_encounters` | `patient_id` (int) | List patient encounters |
| `get_patient_appointments` | `patient_id` (int) | List patient appointments |
| `book_appointment` | `patient_id`, `provider_id`, `start_datetime`, `appointment_type`, `duration_minutes` | Book new appointment |
| `cancel_appointment` | `appointment_id` (int), `reason` (str) | Cancel appointment |
| `get_patient_observations` | `patient_id` (int), `category?` (str) | Get patient observations |

The tool calling loop supports up to 5 iterations per user message, allowing multi-step reasoning (e.g., "Find John Doe and show his vitals" → search → get observations).

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_KEY` | *required* | Google AI API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `GEMINI_MAX_OUTPUT_TOKENS` | `2048` | Max response tokens |
| `GEMINI_TEMPERATURE` | `0.7` | Response creativity (0-1) |
| `WS_MAX_CONNECTIONS` | `100` | Max concurrent WebSocket connections |
| `WS_HEARTBEAT_INTERVAL` | `30` | WebSocket keepalive interval (seconds) |
| `CONVERSATION_TIMEOUT_SECONDS` | `1800` | Session timeout (30 min) |
| `CONVERSATION_MAX_HISTORY` | `50` | Max messages in context window |

## Security

- WebSocket connections require valid JWT token
- All conversations are persisted for HIPAA audit trail
- PHI is never logged or exposed in error messages
- System prompt instructs AI to protect sensitive information
- Tool calls are validated against the database layer

## Database Models

### ConversationSession
- `session_id` (UUID) — unique session identifier
- `user_id` (FK → users) — authenticated user
- `patient_id` (FK → patients, optional) — patient context
- `status` — ACTIVE / PAUSED / COMPLETED / EXPIRED
- `metadata_json` — session metadata

### ConversationMessage
- `session_id` (FK → sessions) — parent session
- `role` — USER / ASSISTANT / SYSTEM / TOOL
- `content` — message text
- `tool_calls` (JSON) — Gemini function call data
- `tool_results` (JSON) — tool execution results
- `tokens_used` — token count for billing
- `latency_ms` — response time tracking
