# Phase 4: LangGraph Multi-Agent + Google Calendar — Implementation

## Overview

Phase 4 transforms APCAN from a single-LLM tool-calling loop into a **LangGraph-powered multi-agent system** with four specialised healthcare agents coordinated by an orchestrator. It also integrates **Google Calendar** for real appointment event synchronisation.

| Metric | Value |
|--------|-------|
| New source files | 8 |
| Modified files | 6 |
| New tests | 45 |
| Total tests | 157 (112 Phase 1-3 + 45 Phase 4) |
| New dependencies | 6 |

## Architecture

```
                    ┌─────────────────────────┐
                    │     Voice WebSocket      │
                    │  (routers/voice.py)      │
                    └───────────┬──────────────┘
                                │  HumanMessage
                                ▼
                    ┌─────────────────────────┐
                    │   Orchestrator Graph     │
                    │  (agents/orchestrator)   │
                    │                         │
                    │  classify_intent → route │
                    └───┬──┬──┬──┬──┬────────┘
                        │  │  │  │  │
             ┌──────────┘  │  │  │  └──────────┐
             ▼             ▼  ▼  ▼             ▼
        ┌─────────┐  ┌────┐┌────┐┌────┐  ┌─────────┐
        │ Intake  │  │Sched││Care││Admin│  │ General │
        │ Agent   │  │Agent││Agt ││Agent│  │Response │
        └─────────┘  └────┘└────┘└────┘  └─────────┘
             │          │     │     │
             └──────────┴─────┴─────┘
                        │
                  ┌─────┴──────┐
                  │ LangGraph  │
                  │   Tools    │
                  │ (10 total) │
                  └─────┬──────┘
                        │
               ┌────────┴─────────┐
               │                  │
          ┌────┴────┐      ┌─────┴─────┐
          │  FHIR   │      │  Google   │
          │  DB     │      │ Calendar  │
          └─────────┘      └───────────┘
```

## What Changed

### New Files Created

| File | Purpose |
|------|---------|
| `app/agents/__init__.py` | Package init, exports `AgentState`, `IntentCategory` |
| `app/agents/state.py` | Shared `AgentState` TypedDict, `IntentCategory` enum, `make_initial_state()` |
| `app/agents/tools.py` | `build_tools(db)` factory — 7 FHIR + 3 Calendar `@tool` functions |
| `app/agents/intake_agent.py` | Intake Agent subgraph — patient registration & identity verification |
| `app/agents/scheduling_agent.py` | Scheduling Agent subgraph — appointment booking with Calendar sync |
| `app/agents/care_agent.py` | Care Agent subgraph — clinical data retrieval & summarisation |
| `app/agents/admin_agent.py` | Admin Agent subgraph — insurance, billing, records queries |
| `app/agents/orchestrator.py` | Top-level orchestrator — intent classification + agent routing |
| `app/services/calendar_service.py` | Google Calendar API client (service account auth) |

### Modified Files

| File | Changes |
|------|---------|
| `app/core/config.py` | Added `GOOGLE_CALENDAR_ID`, `LANGGRAPH_RECURSION_LIMIT`, `LANGGRAPH_MAX_TOOL_ITERATIONS` |
| `app/models/appointment.py` | Added `google_calendar_event_id` column |
| `app/schemas/voice/__init__.py` | Added `WSMessageType.AGENT_SWITCH` |
| `app/routers/voice.py` | Replaced manual tool loop with `orchestrator.ainvoke()` |
| `requirements.txt` | Added 6 new packages |
| `.env.example` | Added Phase 4 settings |

### Key Refactoring

**Before (Phase 3):** `_process_ai_turn()` in voice.py was a manual loop:
```python
result = await gemini_service.send_message(chat, user_text)
while result["tool_calls"] and iteration < 5:
    tool_result = await ai_fhir.execute_tool(...)
    result = await gemini_service.send_tool_result(...)
```

**After (Phase 4):** Single LangGraph graph invocation:
```python
state["messages"] = [HumanMessage(content=user_text)]
result = await orchestrator.ainvoke(state, config={"recursion_limit": 25})
```

## Agent Details

### Intent Classification

The orchestrator uses a zero-temperature Gemini call with a strict classifier prompt to categorise user messages into: `intake`, `scheduling`, `care`, `admin`, or `general`.

### Agent Subgraphs

Each agent is a `StateGraph(AgentState)` with two nodes:
1. **`agent`** — invokes `ChatGoogleGenerativeAI.bind_tools(filtered_tools)` with a specialised system prompt
2. **`tools`** — `ToolNode` that executes tool calls and feeds results back to the agent

The conditional edge `should_continue` checks if the model response contains tool calls. If yes → `tools`, if no → `END`.

### Tool Distribution

| Agent | Tools |
|-------|-------|
| Intake | `search_patients`, `get_patient` |
| Scheduling | `get_patient_appointments`, `book_appointment`, `cancel_appointment`, `check_provider_availability`, `create_calendar_event`, `cancel_calendar_event` |
| Care | `get_patient`, `get_patient_encounters`, `get_patient_observations` |
| Admin | `search_patients`, `get_patient`, `get_patient_encounters` |

### Google Calendar Integration

- **Auth:** Service account (JSON key file or inline JSON string)
- **Operations:** create, update, delete events; list events; check availability
- **Sync:** Uses `asyncio.to_thread()` to run the synchronous Google API client without blocking the event loop
- **Linked via:** `Appointment.google_calendar_event_id` column

## New Dependencies

```
langgraph>=1.0.0
langchain-google-genai>=4.0.0
langchain-core>=0.3.0
google-api-python-client>=2.100.0
google-auth>=2.25.0
google-auth-httplib2>=0.2.0
```

## Test Coverage

45 new tests across 10 test classes:

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestAgentState` | 4 | State creation, defaults, context passing |
| `TestIntentParsing` | 5 | Intent classifier parsing (exact, whitespace, case) |
| `TestToolBuilding` | 8 | Tool factory, filtering, descriptions |
| `TestCalendarService` | 7 | Service account init, create/delete events, availability |
| `TestWSMessageTypePhase4` | 2 | AGENT_SWITCH added, total count |
| `TestAppointmentGoogleCalendarField` | 2 | New column read/write and nullable |
| `TestFHIRToolExecution` | 8 | All 7 FHIR tools execute against test DB |
| `TestAgentGraphBuilds` | 5 | All 4 agents + orchestrator compile successfully |
| `TestPhase4Config` | 3 | New config settings validation |

## Configuration

New `.env` settings:

```env
# LangGraph Multi-Agent (Phase 4)
LANGGRAPH_RECURSION_LIMIT=25
LANGGRAPH_MAX_TOOL_ITERATIONS=10

# Google Calendar
GOOGLE_CALENDAR_ID=primary
GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
```

## Status

✅ **COMPLETED** — All 157 tests passing. Black + Ruff clean.
