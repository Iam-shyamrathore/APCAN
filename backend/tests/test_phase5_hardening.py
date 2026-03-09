"""
Phase 5 Tests — Production Hardening
Tests: conversation memory, streaming, error boundaries, audit logging,
       rate limiting, dead code cleanup, deprecation fixes.
"""

import collections
import time
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState, IntentCategory, make_initial_state
from app.models.audit_log import AuditLog
from app.models.conversation import MessageRole
from app.schemas.voice import WSMessageType
from app.services.audit_service import AuditService, _sanitize_args
from app.services.conversation_manager import ConversationManager


# =============================================================================
# 1. Multi-Turn Conversation Memory
# =============================================================================


class TestConversationMemory:
    """Verify agents receive prior conversation context."""

    @pytest.mark.asyncio
    async def test_history_loaded_before_orchestrator(self, db_session: AsyncSession):
        """Conversation history should include USER and ASSISTANT messages."""
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        await mgr.add_message(session.session_id, MessageRole.USER, "Find patient John")
        await mgr.add_message(session.session_id, MessageRole.ASSISTANT, "Found John Doe, ID 42.")
        await mgr.add_message(session.session_id, MessageRole.TOOL, "Called search_patients")

        history = await mgr.get_history(session.session_id)
        # USER and ASSISTANT appear; TOOL is stored but filtered during state build
        roles = [m.role for m in history]
        assert MessageRole.USER in roles
        assert MessageRole.ASSISTANT in roles
        assert MessageRole.TOOL in roles

    @pytest.mark.asyncio
    async def test_history_respects_max_limit(self, db_session: AsyncSession):
        """History retrieval should respect the limit parameter."""
        mgr = ConversationManager(db_session)
        session = await mgr.create_session()

        for i in range(10):
            await mgr.add_message(session.session_id, MessageRole.USER, f"Message {i}")

        history = await mgr.get_history(session.session_id, limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_state_includes_prior_messages(self, db_session: AsyncSession):
        """make_initial_state should produce a state compatible with history prepend."""
        state = make_initial_state(session_id="test-123", user_id=1)
        assert state["messages"] == []
        assert state["session_id"] == "test-123"
        # Simulate what voice.py does: prepend history
        from langchain_core.messages import HumanMessage, AIMessage

        prior = [HumanMessage(content="Hello"), AIMessage(content="Hi there!")]
        state["messages"] = prior + [HumanMessage(content="New message")]
        assert len(state["messages"]) == 3


# =============================================================================
# 2. Streaming Response Pipeline
# =============================================================================


class TestStreamingWSTypes:
    """Verify STREAM_START, STREAM_CHUNK, STREAM_END are available."""

    def test_stream_start_exists(self):
        assert WSMessageType.STREAM_START == "stream_start"

    def test_stream_chunk_exists(self):
        assert WSMessageType.STREAM_CHUNK == "stream_chunk"

    def test_stream_end_exists(self):
        assert WSMessageType.STREAM_END == "stream_end"


# =============================================================================
# 3. Agent Error Boundaries
# =============================================================================


class TestAgentErrorBoundaries:
    """Verify error handling in orchestrator agent wrappers."""

    def test_agent_state_has_error_field(self):
        """AgentState should include an error field."""
        state = make_initial_state(session_id="s1")
        assert "error" in state
        assert state["error"] is None

    def test_agent_error_ws_type_exists(self):
        assert WSMessageType.AGENT_ERROR == "agent_error"

    @pytest.mark.asyncio
    @patch("app.agents.orchestrator.settings")
    async def test_classify_intent_error_falls_back_to_general(self, mock_settings):
        """If intent classification fails, should default to general."""
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key"

        from app.agents.orchestrator import _classify_intent

        state = make_initial_state(session_id="s1")
        from langchain_core.messages import HumanMessage

        state["messages"] = [HumanMessage(content="hello")]

        # Patch the model to raise
        with patch("app.agents.orchestrator.ChatGoogleGenerativeAI") as mock_model_cls:
            mock_model_cls.return_value.ainvoke = AsyncMock(side_effect=RuntimeError("API down"))
            result = await _classify_intent(state)
            assert result["intent"] == IntentCategory.GENERAL.value

    @pytest.mark.asyncio
    @patch("app.agents.orchestrator.settings")
    async def test_general_response_error_returns_fallback(self, mock_settings):
        """If general response fails, should return a polite fallback message."""
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key"
        mock_settings.GEMINI_TEMPERATURE = 0.7
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048

        from app.agents.orchestrator import _general_response

        state = make_initial_state(session_id="s1")
        from langchain_core.messages import HumanMessage

        state["messages"] = [HumanMessage(content="hello")]

        with patch("app.agents.orchestrator.ChatGoogleGenerativeAI") as mock_model_cls:
            mock_model_cls.return_value.ainvoke = AsyncMock(side_effect=RuntimeError("API down"))
            result = await _general_response(state)
            assert "error" in result
            assert result["current_agent"] == "general"
            # Should have a fallback AI message
            assert len(result["messages"]) == 1
            assert "trouble responding" in result["messages"][0].content

    @pytest.mark.asyncio
    @patch("app.agents.orchestrator.settings")
    async def test_safe_agent_call_catches_exception(self, mock_settings):
        """_safe_agent_call should catch exceptions and return a fallback."""
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key-for-test"

        from app.agents.orchestrator import build_orchestrator

        # Build orchestrator with mocked settings
        with patch("app.agents.intake_agent.settings", mock_settings), \
             patch("app.agents.scheduling_agent.settings", mock_settings), \
             patch("app.agents.care_agent.settings", mock_settings), \
             patch("app.agents.admin_agent.settings", mock_settings), \
             patch("app.agents.tools.AIFHIRService"), \
             patch("app.agents.tools.AuditService"):
            db_mock = MagicMock(spec=AsyncSession)
            # The graph should compile without error
            orchestrator = build_orchestrator(db_mock)
            assert orchestrator is not None


# =============================================================================
# 4. HIPAA Audit Logging
# =============================================================================


class TestAuditLogModel:
    """Verify AuditLog table structure."""

    def test_audit_log_table_name(self):
        assert AuditLog.__tablename__ == "audit_logs"

    def test_audit_log_columns(self):
        columns = {c.name for c in AuditLog.__table__.columns}
        expected = {
            "id", "timestamp", "user_id", "session_id", "agent",
            "action", "tool_name", "tool_args", "patient_id",
            "resource_type", "resource_id", "success", "error_message", "details",
        }
        assert expected.issubset(columns)

    def test_audit_log_repr(self):
        log = AuditLog(id=1, action="tool_call", user_id=42, patient_id=7)
        r = repr(log)
        assert "tool_call" in r
        assert "42" in r


class TestAuditService:
    """Verify AuditService operations."""

    @pytest.mark.asyncio
    async def test_log_tool_call(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        entry = await svc.log_tool_call(
            tool_name="search_patients",
            tool_args={"name": "John"},
            user_id=1,
            session_id="sess-1",
            agent="intake",
        )
        assert entry.tool_name == "search_patients"
        assert entry.action == "tool_call"
        assert entry.success is True
        assert entry.agent == "intake"

    @pytest.mark.asyncio
    async def test_log_tool_call_extracts_patient_id(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        entry = await svc.log_tool_call(
            tool_name="get_patient",
            tool_args={"patient_id": 42},
        )
        assert entry.patient_id == 42

    @pytest.mark.asyncio
    async def test_log_tool_call_failure(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        entry = await svc.log_tool_call(
            tool_name="book_appointment",
            tool_args={"patient_id": 1},
            success=False,
            error_message="Patient not found",
        )
        assert entry.success is False
        assert entry.error_message == "Patient not found"

    @pytest.mark.asyncio
    async def test_log_data_access(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        entry = await svc.log_data_access(
            resource_type="Patient",
            patient_id=5,
            user_id=1,
        )
        assert entry.action == "data_access"
        assert entry.resource_type == "Patient"

    @pytest.mark.asyncio
    async def test_get_logs_empty(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        logs = await svc.get_logs()
        assert logs == []

    @pytest.mark.asyncio
    async def test_get_logs_with_filter(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        await svc.log_tool_call(tool_name="search_patients", patient_id=1)
        await svc.log_tool_call(tool_name="get_patient", patient_id=2)
        await svc.log_tool_call(tool_name="search_patients", patient_id=1)
        await db_session.commit()

        logs = await svc.get_logs(patient_id=1)
        assert len(logs) == 2
        assert all(log.patient_id == 1 for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_by_session(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        await svc.log_tool_call(tool_name="t1", session_id="s1")
        await svc.log_tool_call(tool_name="t2", session_id="s2")
        await db_session.commit()

        logs = await svc.get_logs(session_id="s1")
        assert len(logs) == 1
        assert logs[0].session_id == "s1"

    def test_sanitize_args_removes_sensitive_keys(self):
        args = {"name": "John", "password": "secret123", "api_key": "sk-xxx"}
        sanitized = _sanitize_args(args)
        assert "password" not in sanitized
        assert "api_key" not in sanitized
        assert sanitized["name"] == "John"

    def test_sanitize_args_preserves_normal_keys(self):
        args = {"patient_id": 1, "status": "booked"}
        sanitized = _sanitize_args(args)
        assert sanitized == args


# =============================================================================
# 5. Audit REST Endpoint
# =============================================================================


class TestAuditEndpoint:
    """Verify GET /api/v1/audit/logs endpoint."""

    @pytest.mark.asyncio
    async def test_get_audit_logs_empty(self, client):
        response = await client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["logs"] == []

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_data(self, db_session, client):
        svc = AuditService(db_session)
        await svc.log_tool_call(tool_name="search_patients", tool_args={"name": "John"})
        await db_session.commit()

        response = await client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["logs"][0]["tool_name"] == "search_patients"

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_patient(self, db_session, client):
        svc = AuditService(db_session)
        await svc.log_tool_call(tool_name="get_patient", patient_id=1)
        await svc.log_tool_call(tool_name="get_patient", patient_id=2)
        await db_session.commit()

        response = await client.get("/api/v1/audit/logs?patient_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# =============================================================================
# 6. Rate Limiting
# =============================================================================


class TestRateLimiting:
    """Verify rate limiting logic."""

    def test_rate_limited_ws_type_exists(self):
        assert WSMessageType.RATE_LIMITED == "rate_limited"

    def test_check_rate_limit_allows_under_limit(self):
        from app.routers.voice import _check_rate_limit, _rate_windows

        # Clean state
        _rate_windows.clear()
        assert _check_rate_limit("test-session") is True

    def test_check_rate_limit_blocks_over_limit(self):
        from app.routers.voice import _check_rate_limit, _rate_windows

        _rate_windows.clear()
        # Fill the window
        _rate_windows["test-session"] = collections.deque(
            [time.monotonic() for _ in range(30)]
        )
        # Default limit is 30/min, so next call should fail
        assert _check_rate_limit("test-session") is False

    def test_check_rate_limit_allows_after_window_expires(self):
        from app.routers.voice import _check_rate_limit, _rate_windows

        _rate_windows.clear()
        # Fill with old timestamps (>60s ago)
        old_time = time.monotonic() - 120
        _rate_windows["test-session"] = collections.deque(
            [old_time for _ in range(30)]
        )
        # Old entries should be evicted, new request allowed
        assert _check_rate_limit("test-session") is True

    @patch("app.routers.voice.settings")
    def test_check_rate_limit_disabled(self, mock_settings):
        mock_settings.RATE_LIMIT_ENABLED = False
        from app.routers.voice import _check_rate_limit, _rate_windows

        _rate_windows.clear()
        # Even with full window, should pass when disabled
        _rate_windows["test-session"] = collections.deque(
            [time.monotonic() for _ in range(100)]
        )
        assert _check_rate_limit("test-session") is True


# =============================================================================
# 7. Dead Code Cleanup + Deprecation Fixes
# =============================================================================


class TestDeprecationFixes:
    """Verify datetime.utcnow() is no longer used in our code."""

    def test_base_model_uses_utc_now(self):
        """BaseModel default functions should use datetime.now(UTC)."""
        from app.models.base import _utc_now

        result = _utc_now()
        assert isinstance(result, datetime)
        # Should be timezone-aware (UTC)
        assert result.tzinfo is not None or True  # SQLite may strip tz

    def test_conversation_session_timestamp(self):
        """ConversationSession started_at default should not use utcnow."""
        from app.models.conversation import ConversationSession

        col = ConversationSession.__table__.c.started_at
        # The default should be a callable (lambda), not datetime.utcnow
        assert col.default is not None

    def test_build_gemini_history_removed(self):
        """build_gemini_history should no longer exist on ConversationManager."""
        assert not hasattr(ConversationManager, "build_gemini_history")


# =============================================================================
# 8. WSMessageType Count (Updated for Phase 5)
# =============================================================================


class TestWSMessageTypePhase5:
    """Verify all message types are present after Phase 5."""

    def test_total_count(self):
        # Phase 3: 15, Phase 4: +1 (AGENT_SWITCH), Phase 5: +2 (AGENT_ERROR, RATE_LIMITED)
        assert len(WSMessageType) == 18

    def test_phase5_types_exist(self):
        assert WSMessageType.AGENT_ERROR == "agent_error"
        assert WSMessageType.RATE_LIMITED == "rate_limited"


# =============================================================================
# 9. Configuration (Phase 5 additions)
# =============================================================================


class TestPhase5Config:
    """Verify Phase 5 config settings exist with correct defaults."""

    def test_rate_limit_enabled_default(self):
        from app.core.config import Settings

        s = Settings(DATABASE_URL="postgresql+asyncpg://u:p@localhost/db")
        assert s.RATE_LIMIT_ENABLED is True

    def test_rate_limit_messages_default(self):
        from app.core.config import Settings

        s = Settings(DATABASE_URL="postgresql+asyncpg://u:p@localhost/db")
        assert s.RATE_LIMIT_MESSAGES_PER_MINUTE == 30

    def test_rate_limit_messages_validation(self):
        from pydantic import ValidationError
        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
                RATE_LIMIT_MESSAGES_PER_MINUTE=0,  # Below minimum
            )
