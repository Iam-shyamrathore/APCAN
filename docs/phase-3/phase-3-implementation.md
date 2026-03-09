# Phase 3: Voice AI Integration

**Status**: ✅ COMPLETED  
**Started**: Phase 3 implementation  
**Completed**: All 6 steps implemented, 112 tests passing  
**Objective**: Build real-time Voice AI pipeline using Google Gemini 2.0 Flash with WebSocket streaming

## 📋 Overview

Phase 3 adds the core Voice AI capabilities to APCAN, enabling:

- Real-time voice conversations via WebSocket
- Google Gemini 2.0 Flash for natural language understanding
- AI-powered FHIR queries (natural language → patient data)
- Multi-turn conversation management with context
- Intent classification and command routing
- Appointment scheduling and patient intake via voice

## 🎯 Success Criteria

- [x] Gemini AI service with function calling support
- [x] WebSocket endpoint for real-time voice streaming
- [x] Conversation session persistence (multi-turn dialogue)
- [x] AI-powered FHIR query translation
- [x] Voice command router with intent classification
- [x] Sub-2s response latency for text interactions
- [x] 112 integration tests (all passing)
- [x] Code quality audit (Black, Ruff clean)
- [x] Comprehensive documentation

## 🏗️ Architecture

### Components

```
Client (WebSocket) ──► Voice Router ──► Conversation Manager
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                     ▼
                              Gemini Service        AI FHIR Service
                              (LLM + Tools)       (NL → FHIR Query)
                                    │                     │
                                    ▼                     ▼
                              Function Calling      FHIR Mapper
                              (tool execution)     (DB ↔ FHIR JSON)
```

### New Files

| File                               | Purpose                                            |
| ---------------------------------- | -------------------------------------------------- |
| `models/conversation.py`           | Conversation session & message persistence         |
| `schemas/voice/`                   | WebSocket message schemas, AI response types       |
| `services/gemini_service.py`       | Gemini 2.0 Flash integration with function calling |
| `services/conversation_manager.py` | Multi-turn dialogue state management               |
| `services/ai_fhir_service.py`      | Natural language → FHIR query translation          |
| `routers/voice.py`                 | WebSocket endpoint + voice command routing         |

### Dependencies Added

| Package      | Version | Purpose                         |
| ------------ | ------- | ------------------------------- |
| `websockets` | 12.0    | WebSocket protocol support      |
| `aioredis`   | 2.0.1   | Async Redis for session caching |
| `aiosqlite`  | 0.20.0  | SQLite async for testing        |

## 📐 Implementation Steps

### Step 1: Gemini AI Service Layer

- Gemini 2.0 Flash client initialization
- System prompt engineering for healthcare context
- Function calling schema definition (FHIR tools)
- Streaming response support
- Error handling and retry logic

### Step 2: WebSocket Voice Streaming

- WebSocket endpoint with authentication
- Binary/text message handling
- Connection lifecycle management
- Heartbeat/ping-pong keepalive

### Step 3: Conversation State Management

- ConversationSession SQLAlchemy model
- ConversationMessage model (stores turns)
- Session creation, retrieval, context windowing
- Patient context linking

### Step 4: AI-powered FHIR Queries

- Tool definitions for Gemini function calling
- FHIR query execution from AI tool calls
- Response formatting for voice output
- Patient data summarization

### Step 5: Voice Command Router

- Intent classification via Gemini
- Command routing to services
- Appointment scheduling flow
- Patient lookup flow
- Clinical data retrieval flow

## 🔒 Security Considerations

- JWT authentication on WebSocket upgrade
- Rate limiting per session
- PHI data masking in logs
- Conversation data encrypted at rest
- Session timeout (configurable)
- HIPAA-compliant audit logging for all AI interactions
