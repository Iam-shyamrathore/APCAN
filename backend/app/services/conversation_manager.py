"""
Conversation Manager - Multi-turn dialogue state management.
Handles session lifecycle, message persistence, and context windowing.
"""

import logging
import uuid
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    ConversationStatus,
    MessageRole,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation sessions and history for the voice AI pipeline.
    Persists all messages for HIPAA audit trails.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        user_id: int | None = None,
        patient_id: int | None = None,
        metadata: dict | None = None,
    ) -> ConversationSession:
        """Create a new conversation session."""
        session = ConversationSession(
            session_id=uuid.uuid4().hex,
            user_id=user_id,
            patient_id=patient_id,
            status=ConversationStatus.ACTIVE,
            started_at=datetime.now(UTC),
            metadata_json=metadata,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info("Created conversation session %s", session.session_id)
        return session

    async def get_session(self, session_id: str) -> ConversationSession | None:
        """Get a session by its UUID string."""
        result = await self.db.execute(
            select(ConversationSession)
            .options(selectinload(ConversationSession.messages))
            .where(ConversationSession.session_id == session_id)
            .where(ConversationSession.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def end_session(self, session_id: str) -> ConversationSession | None:
        """Mark a session as completed."""
        session = await self.get_session(session_id)
        if not session:
            return None

        session.status = ConversationStatus.COMPLETED
        session.ended_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info("Ended conversation session %s", session.session_id)
        return session

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        tool_calls: dict | None = None,
        tool_results: dict | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> ConversationMessage:
        """Add a message to the conversation history."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        message = ConversationMessage(
            session_id=session.id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_history(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[ConversationMessage]:
        """
        Get conversation history, most recent first.
        Uses CONVERSATION_MAX_HISTORY from config as default limit.
        """
        max_messages = limit or settings.CONVERSATION_MAX_HISTORY

        session = await self.get_session(session_id)
        if not session:
            return []

        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.created_at.asc())
            .limit(max_messages)
        )
        return list(result.scalars().all())

    async def get_active_sessions_count(self) -> int:
        """Count currently active sessions (for connection limiting)."""
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.status == ConversationStatus.ACTIVE
            )
        )
        return len(result.scalars().all())
