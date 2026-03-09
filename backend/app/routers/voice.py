"""
Voice Router - WebSocket endpoint for real-time voice AI interactions.
Phase 4: LangGraph multi-agent orchestration replaces the manual tool loop.
"""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.conversation import MessageRole
from app.schemas.voice import (
    WSMessageType,
    ConversationSessionResponse,
    ConversationHistoryResponse,
    ConversationMessageResponse,
)
from app.agents.orchestrator import build_orchestrator
from app.agents.state import make_initial_state
from app.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice AI"])

# Track active WebSocket connections (in-process; use Redis for multi-worker)
_active_connections: dict[str, WebSocket] = {}


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

                # Persist user message
                await conversation_mgr.add_message(session.session_id, MessageRole.USER, text)

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
    """
    start = time.monotonic()
    tool_names: list[str] = []

    # Build initial state with the user message
    state = make_initial_state(
        session_id=session_id,
        user_id=user_id,
        patient_context=patient_context,
    )
    state["messages"] = [HumanMessage(content=user_text)]

    # Run the graph
    result = await orchestrator.ainvoke(
        state,
        config={"recursion_limit": settings.LANGGRAPH_RECURSION_LIMIT},
    )

    latency_ms = int((time.monotonic() - start) * 1000)
    agent_name = result.get("current_agent", "general")

    # Notify client which agent handled the request
    await _send_ws(
        websocket,
        WSMessageType.AGENT_SWITCH,
        {"agent": agent_name},
    )

    # Extract tool calls and final text from the message history
    final_text = ""
    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_names.append(tc.get("name", "unknown"))
                    await _send_ws(
                        websocket,
                        WSMessageType.TOOL_CALL,
                        {"tool_name": tc.get("name"), "arguments": tc.get("args", {})},
                    )
            if msg.content:
                final_text = msg.content  # Last AI message is the final response
        elif isinstance(msg, ToolMessage):
            await _send_ws(
                websocket,
                WSMessageType.TOOL_RESULT,
                {"tool_name": msg.name or "unknown", "success": True},
            )
            # Persist tool interaction
            await conversation_mgr.add_message(
                session_id,
                MessageRole.TOOL,
                f"Called {msg.name}",
                tool_calls={"name": msg.name},
                tool_results={"content": msg.content[:500] if msg.content else ""},
            )

    # Persist assistant response
    if final_text:
        await conversation_mgr.add_message(
            session_id,
            MessageRole.ASSISTANT,
            final_text,
            latency_ms=latency_ms,
        )

    return {
        "text": final_text or "I'm sorry, I couldn't process that request. Could you try again?",
        "agent": agent_name,
        "tool_names": tool_names,
        "latency_ms": latency_ms,
        "patient_context": result.get("patient_context", patient_context),
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
