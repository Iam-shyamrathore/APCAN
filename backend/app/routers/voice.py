"""
Voice Router - WebSocket endpoint for real-time voice AI interactions.
Handles: session management, text/audio messaging, tool execution loop.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
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
from app.services.gemini_service import gemini_service
from app.services.conversation_manager import ConversationManager
from app.services.ai_fhir_service import AIFHIRService

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
    ai_fhir = AIFHIRService(db)
    session = None
    chat = None

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

        # Start Gemini chat (fresh session)
        chat = gemini_service.start_chat()

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

                # Send to Gemini and handle tool call loop
                response = await _process_ai_turn(
                    chat, text, ai_fhir, conversation_mgr, session.session_id, websocket
                )

                # Send final text response
                await _send_ws(
                    websocket,
                    WSMessageType.TEXT_RESPONSE,
                    {
                        "text": response["text"],
                        "is_final": True,
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
    chat,
    user_text: str,
    ai_fhir: AIFHIRService,
    conversation_mgr: ConversationManager,
    session_id: str,
    websocket: WebSocket,
) -> dict:
    """
    Process a single AI turn, including iterative tool calling.
    The AI may request multiple sequential tool calls before giving a final text answer.
    """
    total_latency = 0
    tool_names: list[str] = []
    max_tool_iterations = 5  # Safety limit to prevent infinite loops

    # Initial AI call
    result = await gemini_service.send_message(chat, user_text)
    total_latency += result.get("latency_ms", 0)

    iteration = 0
    while result["tool_calls"] and iteration < max_tool_iterations:
        iteration += 1

        for tc in result["tool_calls"]:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_names.append(tool_name)

            # Notify client about tool call
            await _send_ws(
                websocket,
                WSMessageType.TOOL_CALL,
                {
                    "tool_name": tool_name,
                    "arguments": tool_args,
                },
            )

            # Execute tool
            tool_result = await ai_fhir.execute_tool(tool_name, tool_args)

            # Persist tool interaction
            await conversation_mgr.add_message(
                session_id,
                MessageRole.TOOL,
                f"Called {tool_name}",
                tool_calls={"name": tool_name, "args": tool_args},
                tool_results=tool_result,
            )

            # Notify client about tool result
            await _send_ws(
                websocket,
                WSMessageType.TOOL_RESULT,
                {
                    "tool_name": tool_name,
                    "success": tool_result.get("success", False),
                },
            )

            # Send result back to Gemini
            result = await gemini_service.send_tool_result(chat, tool_name, tool_result)
            total_latency += result.get("latency_ms", 0)

    # Persist assistant response
    await conversation_mgr.add_message(
        session_id,
        MessageRole.ASSISTANT,
        result["text"],
        tokens_used=result.get("tokens_used"),
        latency_ms=total_latency,
    )

    return {
        "text": result["text"],
        "tool_names": tool_names,
        "latency_ms": total_latency,
        "tokens_used": result.get("tokens_used"),
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
