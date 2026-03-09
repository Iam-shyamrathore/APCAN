# Phase 5: Production Hardening — Implementation

## Overview

Phase 5 hardens APCAN for production with **streaming responses**, **error boundaries**, **HIPAA audit logging**, **multi-turn memory**, **rate limiting**, and **dead code cleanup**. No new external dependencies — all features leverage existing packages.

| Metric           | Value                            |
| ---------------- | -------------------------------- |
| New source files | 3                                |
| Modified files   | 15                               |
| New tests        | 39                               |
| Total tests      | 195 (156 Phase 1-4 + 39 Phase 5) |
| New dependencies | 0                                |

## Architecture Changes

```
                    ┌─────────────────────────┐
                    │     Voice WebSocket      │
                    │  + Rate Limiter          │
                    │  + Streaming Pipeline    │
                    │  + Conversation Memory   │
                    └───────────┬──────────────┘
                                │
                    ┌───────────┴──────────────┐
                    │   Orchestrator Graph      │
                    │  + Error Boundaries       │
                    │  + _safe_agent_call()     │
                    └───────────┬──────────────┘
                                │
                    ┌───────────┴──────────────┐
                    │     LangGraph Tools       │
                    │  + _audit_fhir() wrapper  │
                    └───────────┬──────────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
         ┌──────────┐   ┌──────────┐   ┌──────────────┐
         │  FHIR DB │   │ Calendar │   │  Audit Logs  │
         └──────────┘   └──────────┘   │  (immutable) │
                                       └──────────────┘
```

## What Changed

### New Files Created

| File                            | Purpose                                              |
| ------------------------------- | ---------------------------------------------------- |
| `app/models/audit_log.py`       | HIPAA-compliant immutable audit log SQLAlchemy model |
| `app/services/audit_service.py` | Audit trail logging and querying service             |
| `app/routers/audit.py`          | REST endpoint for querying audit logs                |

### Modified Files

| File                                   | Changes                                                    |
| -------------------------------------- | ---------------------------------------------------------- |
| `app/routers/voice.py`                 | Conversation memory, streaming, rate limiting, error relay |
| `app/agents/orchestrator.py`           | Error boundaries on all agent nodes                        |
| `app/agents/state.py`                  | Added `error` field to AgentState                          |
| `app/agents/tools.py`                  | Audit logging wrapper for FHIR + Calendar tools            |
| `app/schemas/voice/__init__.py`        | +2 WSMessageType: AGENT_ERROR, RATE_LIMITED                |
| `app/core/config.py`                   | +2 rate limit settings                                     |
| `app/models/__init__.py`               | +AuditLog export                                           |
| `app/models/base.py`                   | datetime.utcnow() → datetime.now(UTC)                      |
| `app/models/conversation.py`           | datetime.utcnow() → datetime.now(UTC)                      |
| `app/core/security.py`                 | datetime.utcnow() → datetime.now(UTC)                      |
| `app/services/conversation_manager.py` | datetime.utcnow() → datetime.now(UTC), removed dead code   |
| `app/main.py`                          | +audit router registration                                 |
| `tests/test_phase4_agents.py`          | Updated WSMessageType count (18)                           |
| `tests/test_conversation_manager.py`   | Removed dead test                                          |
| `tests/test_voice.py`                  | datetime.utcnow() → datetime.now(UTC)                      |

## Feature Details

### 1. Multi-Turn Conversation Memory

The voice WebSocket handler now loads prior conversation history before invoking the orchestrator. Messages are converted from the database format to LangChain `HumanMessage`/`AIMessage` objects and prepended to the state.

**Flow:**

1. User sends TEXT_INPUT via WebSocket
2. `conversation_mgr.get_history(session_id)` retrieves prior messages
3. Messages converted to LangChain types and prepended to `state["messages"]`
4. Orchestrator sees full dialogue context

### 2. Streaming Response Pipeline

Replaced synchronous `orchestrator.ainvoke()` with LangGraph's `astream_events(version="v2")`. Token-by-token streaming via WebSocket:

| Event                  | WebSocket Message      | Description                  |
| ---------------------- | ---------------------- | ---------------------------- |
| `on_chain_start`       | (agent tracking)       | Track active agent           |
| `on_chat_model_stream` | STREAM_START/CHUNK/END | Token-by-token text delivery |
| `on_tool_start`        | TOOL_CALL              | Tool invocation notification |
| `on_tool_end`          | TOOL_RESULT            | Tool result delivery         |
| `on_chain_end`         | (state extraction)     | Extract final state          |

**Fallback:** If streaming raises an exception, falls back to `orchestrator.ainvoke()`.

### 3. Agent Error Boundaries

Every agent node is wrapped with `_safe_agent_call()`:

```python
async def _safe_agent_call(name: str, graph, state: AgentState) -> AgentState:
    try:
        return await graph.ainvoke(state)
    except Exception:
        return {**state, "error": f"{name} failed", "messages": [fallback_msg]}
```

Also applied to `_classify_intent()` (defaults to GENERAL) and `_general_response()` (returns polite fallback).

### 4. HIPAA Audit Logging

**AuditLog model** — Immutable records. Extends `Base` directly (no soft delete).

| Field         | Type          | Description                         |
| ------------- | ------------- | ----------------------------------- |
| timestamp     | DateTime(UTC) | When the action occurred            |
| user_id       | FK → users    | Who performed the action            |
| session_id    | String        | WebSocket session ID                |
| agent         | String        | Which agent was active              |
| action        | String        | tool_call / data_access             |
| tool_name     | String        | Name of the tool called             |
| tool_args     | JSON          | Arguments (sensitive keys stripped) |
| patient_id    | FK → patients | Patient involved (if any)           |
| resource_type | String        | FHIR resource type                  |
| success       | Boolean       | Whether the call succeeded          |
| error_message | String        | Error details (if failed)           |

**Sensitive arg sanitization:** `_sanitize_args()` strips `password`, `token`, `secret`, `api_key`, `credentials` before persisting.

**REST endpoint:** `GET /api/v1/audit/logs` with filters: `patient_id`, `user_id`, `session_id`, `action`, `limit`.

### 5. Rate Limiting

Sliding-window rate limiter per WebSocket session:

- **Window:** 60 seconds
- **Default limit:** 30 messages/minute
- **Storage:** In-memory `collections.deque` per session
- **Configurable:** `RATE_LIMIT_ENABLED`, `RATE_LIMIT_MESSAGES_PER_MINUTE`
- **WebSocket message:** `RATE_LIMITED` sent when exceeded

### 6. Dead Code + Deprecation Cleanup

- Removed `ConversationManager.build_gemini_history()` — dead since Phase 4 LangGraph migration
- Replaced all `datetime.utcnow()` → `datetime.now(UTC)` across 6 files (Python 3.12+ deprecation)
- Added `_utc_now()` helper in `base.py` for SQLAlchemy column defaults

## Configuration

New settings added to `app/core/config.py`:

```python
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_MESSAGES_PER_MINUTE: int = 30  # 1-300 range validated
```

## Testing

39 new tests across 9 test classes:

| Class                    | Tests | Coverage                                   |
| ------------------------ | ----- | ------------------------------------------ |
| TestConversationMemory   | 3     | History loading, limits, state prepend     |
| TestStreamingWSTypes     | 3     | STREAM_START/CHUNK/END existence           |
| TestAgentErrorBoundaries | 5     | Error field, fallbacks, safe agent call    |
| TestAuditLogModel        | 3     | Table structure, columns, repr             |
| TestAuditService         | 9     | Tool calls, data access, filters, sanitize |
| TestAuditEndpoint        | 3     | REST endpoint empty/data/filtered          |
| TestRateLimiting         | 4     | Under/over limit, window expiry, disabled  |
| TestDeprecationFixes     | 3     | UTC helpers, removed dead code             |
| TestWSMessageTypePhase5  | 2     | Count (18), new types exist                |
| TestPhase5Config         | 3     | Default values, validation                 |

## Success Criteria

- [x] Multi-turn conversation memory — agents see full dialogue context
- [x] Streaming responses — token-by-token delivery via WebSocket
- [x] Error boundaries — graceful fallback on agent/tool failures
- [x] HIPAA audit logging — immutable trail with sensitive data filtering
- [x] Rate limiting — configurable per-session sliding window
- [x] Dead code removed — build_gemini_history eliminated
- [x] Deprecation fixes — zero utcnow() warnings from our code
- [x] 195/195 tests passing
