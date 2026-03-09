"""
Conversation Models - Voice AI session and message persistence
HIPAA-compliant conversation tracking for audit trails
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ConversationStatus(str, enum.Enum):
    """Conversation session states"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


class MessageRole(str, enum.Enum):
    """Message sender role in conversation"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ConversationSession(BaseModel):
    """
    Tracks a voice/chat conversation session.
    Each session links to a patient and/or user for HIPAA audit.
    """

    __tablename__ = "conversation_sessions"

    session_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, doc="UUID for WebSocket session"
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, doc="Authenticated user"
    )
    patient_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("patients.id"), nullable=True, doc="Patient context for this session"
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus),
        default=ConversationStatus.ACTIVE,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, doc="Extra session metadata (device, language, etc.)"
    )

    # Relationships
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ConversationMessage(BaseModel):
    """
    Individual message in a conversation session.
    Stores both user input and AI responses for audit trail.
    """

    __tablename__ = "conversation_messages"

    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_sessions.id"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole), nullable=False, doc="Who sent this message"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, doc="Message text content")
    tool_calls: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, doc="Function calls made by the AI"
    )
    tool_results: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, doc="Results returned from tool execution"
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer, nullable=True, doc="Token count for billing/monitoring"
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, doc="Response latency in milliseconds"
    )

    # Relationship
    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession", back_populates="messages"
    )
