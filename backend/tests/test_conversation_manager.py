"""
Tests for Conversation Manager - session lifecycle and message persistence.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationStatus, MessageRole
from app.services.conversation_manager import ConversationManager


pytestmark = pytest.mark.asyncio


class TestConversationManager:
    """Tests for ConversationManager service."""

    async def test_create_session(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session(user_id=None, patient_id=None)

        assert session.session_id is not None
        assert len(session.session_id) == 32  # uuid4 hex
        assert session.status == ConversationStatus.ACTIVE
        assert session.started_at is not None

    async def test_create_session_with_context(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session(
            user_id=1,
            patient_id=2,
            metadata={"language": "en", "device": "mobile"},
        )

        assert session.user_id == 1
        assert session.patient_id == 2
        assert session.metadata_json["language"] == "en"

    async def test_get_session(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        created = await mgr.create_session()

        retrieved = await mgr.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    async def test_get_session_not_found(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        result = await mgr.get_session("nonexistent_session_id")
        assert result is None

    async def test_end_session(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        ended = await mgr.end_session(session.session_id)
        assert ended is not None
        assert ended.status == ConversationStatus.COMPLETED
        assert ended.ended_at is not None

    async def test_end_session_not_found(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        result = await mgr.end_session("nonexistent")
        assert result is None

    async def test_add_message(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        msg = await mgr.add_message(
            session.session_id,
            role=MessageRole.USER,
            content="Hello, I need help with my appointment.",
        )

        assert msg.id is not None
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, I need help with my appointment."

    async def test_add_message_with_tools(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        msg = await mgr.add_message(
            session.session_id,
            role=MessageRole.TOOL,
            content="Called search_patients",
            tool_calls={"name": "search_patients", "args": {"name": "John"}},
            tool_results={"success": True, "data": {"total": 1}},
            tokens_used=150,
            latency_ms=320,
        )

        assert msg.tool_calls["name"] == "search_patients"
        assert msg.tool_results["success"] is True
        assert msg.tokens_used == 150
        assert msg.latency_ms == 320

    async def test_add_message_invalid_session(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)

        with pytest.raises(ValueError, match="not found"):
            await mgr.add_message("bad_session", MessageRole.USER, "test")

    async def test_get_history(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        await mgr.add_message(session.session_id, MessageRole.USER, "First message")
        await mgr.add_message(session.session_id, MessageRole.ASSISTANT, "First response")
        await mgr.add_message(session.session_id, MessageRole.USER, "Second message")

        history = await mgr.get_history(session.session_id)
        assert len(history) == 3
        assert history[0].content == "First message"
        assert history[1].content == "First response"
        assert history[2].content == "Second message"

    async def test_get_history_with_limit(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        for i in range(10):
            await mgr.add_message(session.session_id, MessageRole.USER, f"Message {i}")

        history = await mgr.get_history(session.session_id, limit=5)
        assert len(history) == 5

    async def test_get_history_empty_session(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        history = await mgr.get_history(session.session_id)
        assert history == []

    async def test_build_gemini_history(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        await mgr.add_message(session.session_id, MessageRole.USER, "What are my appointments?")
        await mgr.add_message(
            session.session_id, MessageRole.ASSISTANT, "You have 2 upcoming appointments."
        )
        await mgr.add_message(
            session.session_id, MessageRole.TOOL, "Called get_patient_appointments"
        )

        history = await mgr.get_history(session.session_id)
        gemini_history = mgr.build_gemini_history(history)

        # TOOL and SYSTEM messages are excluded from Gemini history
        assert len(gemini_history) == 2
        assert gemini_history[0]["role"] == "user"
        assert gemini_history[1]["role"] == "model"

    async def test_get_active_sessions_count(self, db_session: AsyncSession):
        mgr = ConversationManager(db_session)

        await mgr.create_session()
        await mgr.create_session()
        s3 = await mgr.create_session()
        await mgr.end_session(s3.session_id)

        count = await mgr.get_active_sessions_count()
        assert count == 2
