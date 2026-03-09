"""
Tests for Voice WebSocket endpoint and REST conversation APIs.
"""

import pytest

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationStatus
from app.services.conversation_manager import ConversationManager
from app.schemas.voice import WSMessageType


pytestmark = pytest.mark.asyncio


class TestVoiceRESTEndpoints:
    """Tests for conversation REST API endpoints."""

    async def test_get_session_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/voice/sessions/nonexistent")
        assert resp.status_code == 404

    async def test_end_session_not_found(self, client: AsyncClient):
        resp = await client.post("/api/v1/voice/sessions/nonexistent/end")
        assert resp.status_code == 404

    async def test_get_session_history(self, client: AsyncClient, db_session: AsyncSession):
        # Create a session directly
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()
        from app.models.conversation import MessageRole

        await mgr.add_message(session.session_id, MessageRole.USER, "Hello")
        await mgr.add_message(session.session_id, MessageRole.ASSISTANT, "Hi there!")

        resp = await client.get(f"/api/v1/voice/sessions/{session.session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["session"]["session_id"] == session.session_id
        assert data["session"]["status"] == "active"
        assert data["session"]["message_count"] == 2
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["role"] == "assistant"

    async def test_end_session(self, client: AsyncClient, db_session: AsyncSession):
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        resp = await client.post(f"/api/v1/voice/sessions/{session.session_id}/end")
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "completed"
        assert data["ended_at"] is not None


class TestVoiceSchemas:
    """Test voice schema validation."""

    def test_ws_message_types(self):
        assert WSMessageType.TEXT_INPUT == "text_input"
        assert WSMessageType.TEXT_RESPONSE == "text_response"
        assert WSMessageType.SESSION_CREATED == "session_created"
        assert WSMessageType.ERROR == "error"
        assert WSMessageType.TOOL_CALL == "tool_call"
        assert WSMessageType.TOOL_RESULT == "tool_result"

    def test_text_input_validation(self):
        from app.schemas.voice import TextInputMessage

        msg = TextInputMessage(text="Hello")
        assert msg.text == "Hello"

        with pytest.raises(Exception):
            TextInputMessage(text="")  # min_length=1

    def test_text_response(self):
        from app.schemas.voice import TextResponseMessage

        msg = TextResponseMessage(
            text="Response here",
            is_final=True,
            tool_calls_made=["search_patients"],
            latency_ms=250,
        )
        assert msg.is_final is True
        assert msg.tool_calls_made == ["search_patients"]

    def test_ai_tool_call_schema(self):
        from app.schemas.voice import AIToolCall, AIToolResult

        call = AIToolCall(tool_name="get_patient", arguments={"patient_id": 1})
        assert call.tool_name == "get_patient"

        result = AIToolResult(tool_name="get_patient", success=True, data={"name": "John"})
        assert result.success is True

    def test_conversation_session_response(self):
        from app.schemas.voice import ConversationSessionResponse
        from datetime import datetime, UTC

        resp = ConversationSessionResponse(
            session_id="abc123",
            status="active",
            started_at=datetime.now(UTC),
            message_count=5,
        )
        assert resp.session_id == "abc123"
        assert resp.message_count == 5


class TestConversationModel:
    """Tests for the Conversation SQLAlchemy models."""

    async def test_create_session_model(self, db_session: AsyncSession):
        from app.models.conversation import ConversationSession

        session = ConversationSession(
            session_id="test_session_123",
            status=ConversationStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.session_id == "test_session_123"
        assert session.status == ConversationStatus.ACTIVE

    async def test_create_message_model(self, db_session: AsyncSession):
        from app.models.conversation import (
            ConversationSession,
            ConversationMessage,
            MessageRole,
        )

        session = ConversationSession(
            session_id="msg_test_session",
            status=ConversationStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        message = ConversationMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content="Test message content",
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        assert message.id is not None
        assert message.role == MessageRole.USER
        assert message.content == "Test message content"

    async def test_session_message_relationship(self, db_session: AsyncSession):
        from app.models.conversation import (
            ConversationSession,
            ConversationMessage,
            MessageRole,
        )

        session = ConversationSession(
            session_id="rel_test_session",
            status=ConversationStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        for i in range(3):
            msg = ConversationMessage(
                session_id=session.id,
                role=MessageRole.USER,
                content=f"Message {i}",
            )
            db_session.add(msg)
        await db_session.commit()

        # Reload with relationship
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(ConversationSession)
            .options(selectinload(ConversationSession.messages))
            .where(ConversationSession.session_id == "rel_test_session")
        )
        loaded = result.scalar_one()
        assert len(loaded.messages) == 3
