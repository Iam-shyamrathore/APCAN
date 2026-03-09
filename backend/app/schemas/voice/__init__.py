"""
Voice AI Schemas - WebSocket messages, conversation, and AI response types
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, UTC
from enum import Enum


# --- WebSocket Message Types ---


class WSMessageType(str, Enum):
    """WebSocket message types for client-server communication"""

    # Client → Server
    TEXT_INPUT = "text_input"
    AUDIO_CHUNK = "audio_chunk"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PING = "ping"

    # Server → Client
    TEXT_RESPONSE = "text_response"
    AUDIO_RESPONSE = "audio_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SESSION_CREATED = "session_created"
    PONG = "pong"
    STREAM_START = "stream_start"
    STREAM_CHUNK = "stream_chunk"
    STREAM_END = "stream_end"
    AGENT_SWITCH = "agent_switch"
    AGENT_ERROR = "agent_error"
    RATE_LIMITED = "rate_limited"


class WSMessage(BaseModel):
    """Base WebSocket message envelope"""

    type: WSMessageType
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    session_id: Optional[str] = None


class SessionStartRequest(BaseModel):
    """Client request to start a new conversation session"""

    patient_id: Optional[int] = Field(None, description="Link session to a patient context")
    language: str = Field(default="en", description="Preferred language")
    metadata: Optional[dict] = None


class TextInputMessage(BaseModel):
    """Client sends text input"""

    text: str = Field(..., min_length=1, max_length=4096, description="User message text")


class TextResponseMessage(BaseModel):
    """Server sends text response"""

    text: str
    is_final: bool = Field(default=True, description="False if streaming partial response")
    tool_calls_made: list[str] = Field(default_factory=list)
    latency_ms: Optional[int] = None


class StreamChunkMessage(BaseModel):
    """Server sends streaming text chunk"""

    chunk: str
    chunk_index: int = 0


# --- Conversation Schemas ---


class ConversationSessionResponse(BaseModel):
    """API response for conversation session"""

    session_id: str
    status: str
    patient_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    """API response for a conversation message"""

    id: int
    role: str
    content: str
    tool_calls: Optional[dict] = None
    tool_results: Optional[dict] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistoryResponse(BaseModel):
    """Full conversation history"""

    session: ConversationSessionResponse
    messages: list[ConversationMessageResponse] = []


# --- AI Tool Call Schemas ---


class AIToolCall(BaseModel):
    """Represents a tool/function call made by the AI"""

    tool_name: str
    arguments: dict = Field(default_factory=dict)


class AIToolResult(BaseModel):
    """Result from executing an AI tool call"""

    tool_name: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class AIResponse(BaseModel):
    """Complete AI response including tool calls"""

    text: str
    tool_calls: list[AIToolCall] = Field(default_factory=list)
    tool_results: list[AIToolResult] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    model: str = "gemini-2.0-flash"
