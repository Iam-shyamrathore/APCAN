"""
Voice Router - WebSocket endpoint for real-time voice AI interactions.
Phase 4: LangGraph multi-agent orchestration replaces the manual tool loop.
Phase 5: Multi-turn conversation memory, streaming, error boundaries.
"""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import MessageRole as _MessageRole

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.voice import (
    WSMessageType,
    ConversationSessionResponse,
    ConversationHistoryResponse,
    ConversationMessageResponse,
)
from app.agents.orchestrator import build_orchestrator
from app.agents.state import make_initial_state
from app.services.conversation_manager import ConversationManager

import collections

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice AI"])

# Track active WebSocket connections (in-process; use Redis for multi-worker)
_active_connections: dict[str, WebSocket] = {}

# Phase 5: Per-session sliding window rate limiter (in-memory)
_rate_windows: dict[str, collections.deque] = {}


def _check_rate_limit(session_id: str) -> bool:
    """
    Return True if the request is within rate limits, False if exceeded.
    Uses a sliding window of timestamps per session.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return True

    now = time.monotonic()
    window = _rate_windows.setdefault(session_id, collections.deque())

    # Remove timestamps older than 60 seconds
    cutoff = now - 60.0
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) >= settings.RATE_LIMIT_MESSAGES_PER_MINUTE:
        return False

    window.append(now)
    return True


def _authenticate_ws_token(token: str | None) -> dict | None:
    """
    Validate JWT token for WebSocket connections.
    Returns decoded payload or None if invalid/missing.
    """
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Main WebSocket endpoint for voice AI conversations.

    Connection flow:
    1. Client connects with ?token=<JWT> query param
    2. Server sends session_created message
    3. Client sends text_input / audio_chunk messages
    4. Server responds with text_response / tool events
    5. Either side can close the connection

    Message format (JSON):
        {"type": "<WSMessageType>", "data": {...}, "session_id": "..."}
    """
    # Authenticate
    user_payload = _authenticate_ws_token(token)
    user_id = int(user_payload["sub"]) if user_payload and "sub" in user_payload else None

    # Check connection limit
    if len(_active_connections) >= settings.WS_MAX_CONNECTIONS:
        await websocket.close(code=1013, reason="Max connections reached")
        return

    await websocket.accept()

    conversation_mgr = ConversationManager(db)
    orchestrator = build_orchestrator(db)
    session = None
    patient_context: dict = {}

    try:
        # Create conversation session
        session = await conversation_mgr.create_session(user_id=user_id)
        _active_connections[session.session_id] = websocket

        # Send session_created event
        await _send_ws(
            websocket,
            WSMessageType.SESSION_CREATED,
            {
                "session_id": session.session_id,
                "message": "Connected to APCAN Voice AI. How can I help you today?",
            },
        )

        # Message loop
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_ws(websocket, WSMessageType.ERROR, {"error": "Invalid JSON message"})
                continue

            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == WSMessageType.PING:
                await _send_ws(websocket, WSMessageType.PONG, {})

            elif msg_type == WSMessageType.TEXT_INPUT:
                text = data.get("text", "").strip()
                if not text:
                    await _send_ws(websocket, WSMessageType.ERROR, {"error": "Empty text input"})
                    continue

                # Phase 5: Rate limiting
                if not _check_rate_limit(session.session_id):
                    await _send_ws(
                        websocket,
                        WSMessageType.RATE_LIMITED,
                        {"error": "Rate limit exceeded. Please wait before sending more messages."},
                    )
                    continue

                # Persist user message
                await conversation_mgr.add_message(session.session_id, _MessageRole.USER, text)

                # Run through LangGraph orchestrator
                response = await _process_ai_turn(
                    orchestrator,
                    text,
                    conversation_mgr,
                    session.session_id,
                    user_id,
                    patient_context,
                    websocket,
                )

                # Update patient context for future turns
                if response.get("patient_context"):
                    patient_context = response["patient_context"]

                # Phase 5: Notify client if an agent error occurred
                if response.get("error"):
                    await _send_ws(
                        websocket,
                        WSMessageType.AGENT_ERROR,
                        {"error": response["error"], "agent": response.get("agent", "unknown")},
                    )

                # Send final text response
                await _send_ws(
                    websocket,
                    WSMessageType.TEXT_RESPONSE,
                    {
                        "text": response["text"],
                        "is_final": True,
                        "agent": response.get("agent", "general"),
                        "tool_calls_made": response.get("tool_names", []),
                        "latency_ms": response.get("latency_ms"),
                    },
                )

            elif msg_type == WSMessageType.SESSION_START:
                # Update patient context if provided
                patient_id = data.get("patient_id")
                if patient_id and session:
                    session.patient_id = patient_id
                    await db.commit()
                await _send_ws(
                    websocket,
                    WSMessageType.SESSION_CREATED,
                    {
                        "session_id": session.session_id,
                        "patient_id": patient_id,
                    },
                )

            elif msg_type == WSMessageType.SESSION_END:
                break  # Client requested close

            else:
                await _send_ws(
                    websocket, WSMessageType.ERROR, {"error": f"Unknown message type: {msg_type}"}
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session.session_id if session else "unknown")
    except Exception:
        logger.exception("WebSocket error")
        try:
            await _send_ws(websocket, WSMessageType.ERROR, {"error": "Internal server error"})
        except Exception:
            pass
    finally:
        # Cleanup
        if session:
            _active_connections.pop(session.session_id, None)
            _rate_windows.pop(session.session_id, None)
            await conversation_mgr.end_session(session.session_id)


async def _process_ai_turn(
    orchestrator,
    user_text: str,
    conversation_mgr: ConversationManager,
    session_id: str,
    user_id: int | None,
    patient_context: dict,
    websocket: WebSocket,
) -> dict:
    """
    Process a single AI turn via the LangGraph orchestrator.

    The orchestrator classifies intent → routes to the appropriate agent →
    the agent uses tools autonomously via its subgraph → returns final text.

    Phase 5: Loads prior conversation history so agents have multi-turn context.
    Phase 5: Streams tokens via astream_events() for real-time voice UX.
    """
    start = time.monotonic()
    tool_names: list[str] = []

    # --- Phase 5: Load conversation history for multi-turn context ---
    prior_messages: list[HumanMessage | AIMessage] = []
    try:
        history = await conversation_mgr.get_history(session_id)
        for msg in history:
            if msg.role == _MessageRole.USER:
                prior_messages.append(HumanMessage(content=msg.content))
            elif msg.role == _MessageRole.ASSISTANT:
                prior_messages.append(AIMessage(content=msg.content))
    except Exception:
        logger.warning("Failed to load conversation history for session %s", session_id)

    # Build initial state with history + current user message
    state = make_initial_state(
        session_id=session_id,
        user_id=user_id,
        patient_context=patient_context,
    )
    state["messages"] = prior_messages + [HumanMessage(content=user_text)]

    config = {"recursion_limit": settings.LANGGRAPH_RECURSION_LIMIT}

    # --- Phase 5: Streaming response via astream_events() ---
    final_text = ""
    agent_name = "general"
    collected_patient_context = patient_context
    streaming_started = False
    chunk_index = 0
    agent_error: str | None = None

    try:
        async for event in orchestrator.astream_events(state, config=config, version="v2"):
            kind = event.get("event", "")

            # Track which agent is active
            if kind == "on_chain_start" and event.get("name") in (
                "intake",
                "scheduling",
                "care",
                "admin",
                "general",
            ):
                agent_name = event["name"]
                await _send_ws(
                    websocket,
                    WSMessageType.AGENT_SWITCH,
                    {"agent": agent_name},
                )

            # Stream LLM tokens to client
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if not streaming_started:
                        await _send_ws(
                            websocket,
                            WSMessageType.STREAM_START,
                            {"agent": agent_name},
                        )
                        streaming_started = True
                    await _send_ws(
                        websocket,
                        WSMessageType.STREAM_CHUNK,
                        {"chunk": chunk.content, "chunk_index": chunk_index},
                    )
                    chunk_index += 1

            # Capture tool calls
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_names.append(tool_name)
                await _send_ws(
                    websocket,
                    WSMessageType.TOOL_CALL,
                    {"tool_name": tool_name, "arguments": event.get("data", {}).get("input", {})},
                )

            # Capture tool results
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                output = event.get("data", {}).get("output", "")
                await _send_ws(
                    websocket,
                    WSMessageType.TOOL_RESULT,
                    {"tool_name": tool_name, "success": True},
                )
                # Persist tool interaction
                content_str = str(output)[:500] if output else ""
                await conversation_mgr.add_message(
                    session_id,
                    _MessageRole.TOOL,
                    f"Called {tool_name}",
                    tool_calls={"name": tool_name},
                    tool_results={"content": content_str},
                )

            # Capture final state from chain end
            elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                result = event.get("data", {}).get("output", {})
                if isinstance(result, dict):
                    agent_name = result.get("current_agent", agent_name)
                    collected_patient_context = result.get(
                        "patient_context", patient_context
                    )
                    agent_error = result.get("error")
                    # Extract final text from last AI message
                    for msg in reversed(result.get("messages", [])):
                        if isinstance(msg, AIMessage) and msg.content:
                            final_text = msg.content
                            break

        if streaming_started:
            await _send_ws(
                websocket,
                WSMessageType.STREAM_END,
                {"agent": agent_name},
            )

    except Exception:
        logger.exception("Streaming failed for session %s, falling back", session_id)
        # Fallback: non-streaming ainvoke
        result = await orchestrator.ainvoke(state, config=config)
        agent_name = result.get("current_agent", "general")
        collected_patient_context = result.get("patient_context", patient_context)
        await _send_ws(
            websocket, WSMessageType.AGENT_SWITCH, {"agent": agent_name}
        )
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and msg.content:
                final_text = msg.content
            elif isinstance(msg, ToolMessage):
                await _send_ws(
                    websocket,
                    WSMessageType.TOOL_RESULT,
                    {"tool_name": msg.name or "unknown", "success": True},
                )

    latency_ms = int((time.monotonic() - start) * 1000)

    # Persist assistant response
    if final_text:
        await conversation_mgr.add_message(
            session_id,
            _MessageRole.ASSISTANT,
            final_text,
            latency_ms=latency_ms,
        )

    return {
        "text": final_text or "I'm sorry, I couldn't process that request. Could you try again?",
        "agent": agent_name,
        "tool_names": tool_names,
        "latency_ms": latency_ms,
        "patient_context": collected_patient_context,
        "error": agent_error,
    }



async def _send_ws(websocket: WebSocket, msg_type: WSMessageType, data: dict) -> None:
    """Send a typed JSON message over WebSocket."""
    await websocket.send_json(
        {
            "type": msg_type.value,
            "data": data,
        }
    )


# --- REST Endpoints for conversation history ---


@router.get(
    "/sessions/{session_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history",
)
async def get_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full conversation session with messages."""
    mgr = ConversationManager(db)
    session = await mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await mgr.get_history(session_id)

    return ConversationHistoryResponse(
        session=ConversationSessionResponse(
            session_id=session.session_id,
            status=session.status.value,
            patient_id=session.patient_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            message_count=len(messages),
        ),
        messages=[
            ConversationMessageResponse(
                id=m.id,
                role=m.role.value,
                content=m.content,
                tool_calls=m.tool_calls,
                tool_results=m.tool_results,
                tokens_used=m.tokens_used,
                latency_ms=m.latency_ms,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.post(
    "/sessions/{session_id}/end",
    response_model=ConversationSessionResponse,
    summary="End a conversation session",
)
async def end_conversation_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """End an active conversation session."""
    mgr = ConversationManager(db)
    session = await mgr.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await mgr.get_history(session_id)

    return ConversationSessionResponse(
        session_id=session.session_id,
        status=session.status.value,
        patient_id=session.patient_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=len(messages),
    )
