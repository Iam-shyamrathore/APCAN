"""
Tests for Phase 4: Agent state, tools, calendar service, and intent parsing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import IntentCategory, make_initial_state
from app.agents.tools import (
    build_tools,
    filter_tools,
    INTAKE_TOOLS,
    SCHEDULING_TOOLS,
    CARE_TOOLS,
    ADMIN_TOOLS,
)
from app.agents.orchestrator import _parse_intent
from app.schemas.voice import WSMessageType


pytestmark = pytest.mark.asyncio


# --- Agent State Tests ---


class TestAgentState:
    """Tests for AgentState TypedDict and helper functions."""

    def test_make_initial_state(self):
        state = make_initial_state(session_id="test-123", user_id=42)
        assert state["session_id"] == "test-123"
        assert state["user_id"] == 42
        assert state["current_agent"] == "orchestrator"
        assert state["intent"] == IntentCategory.GENERAL.value
        assert state["messages"] == []
        assert state["patient_context"] == {}
        assert state["tool_results"] == []
        assert state["metadata"] == {}

    def test_make_initial_state_with_context(self):
        ctx = {"id": 1, "name": "John Doe"}
        state = make_initial_state(
            session_id="s1",
            patient_context=ctx,
            metadata={"language": "en"},
        )
        assert state["patient_context"] == ctx
        assert state["metadata"]["language"] == "en"

    def test_make_initial_state_defaults(self):
        state = make_initial_state(session_id="s2")
        assert state["user_id"] is None
        assert state["patient_context"] == {}

    def test_intent_category_values(self):
        assert IntentCategory.INTAKE.value == "intake"
        assert IntentCategory.SCHEDULING.value == "scheduling"
        assert IntentCategory.CARE.value == "care"
        assert IntentCategory.ADMIN.value == "admin"
        assert IntentCategory.GENERAL.value == "general"


# --- Intent Parsing Tests ---


class TestIntentParsing:
    """Tests for the orchestrator's intent classifier."""

    def test_parse_exact_intents(self):
        assert _parse_intent("scheduling") == IntentCategory.SCHEDULING
        assert _parse_intent("intake") == IntentCategory.INTAKE
        assert _parse_intent("care") == IntentCategory.CARE
        assert _parse_intent("admin") == IntentCategory.ADMIN
        assert _parse_intent("general") == IntentCategory.GENERAL

    def test_parse_intent_with_whitespace(self):
        assert _parse_intent("  scheduling  ") == IntentCategory.SCHEDULING
        assert _parse_intent("\ncare\n") == IntentCategory.CARE

    def test_parse_intent_with_period(self):
        assert _parse_intent("scheduling.") == IntentCategory.SCHEDULING
        assert _parse_intent("Care.") == IntentCategory.CARE

    def test_parse_intent_case_insensitive(self):
        assert _parse_intent("SCHEDULING") == IntentCategory.SCHEDULING
        assert _parse_intent("Intake") == IntentCategory.INTAKE

    def test_parse_intent_unknown(self):
        assert _parse_intent("blahblah") == IntentCategory.GENERAL
        assert _parse_intent("") == IntentCategory.GENERAL


# --- Tool Building Tests ---


class TestToolBuilding:
    """Tests for the build_tools factory and tool filtering."""

    def test_build_tools_returns_10(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        assert len(tools) == 10

    def test_tool_names(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        names = {t.name for t in tools}
        expected = {
            "search_patients",
            "get_patient",
            "get_patient_encounters",
            "get_patient_appointments",
            "book_appointment",
            "cancel_appointment",
            "get_patient_observations",
            "check_provider_availability",
            "create_calendar_event",
            "cancel_calendar_event",
        }
        assert names == expected

    def test_filter_intake_tools(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        filtered = filter_tools(tools, INTAKE_TOOLS)
        names = {t.name for t in filtered}
        assert names == {"search_patients", "get_patient"}

    def test_filter_scheduling_tools(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        filtered = filter_tools(tools, SCHEDULING_TOOLS)
        names = {t.name for t in filtered}
        assert names == SCHEDULING_TOOLS

    def test_filter_care_tools(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        filtered = filter_tools(tools, CARE_TOOLS)
        names = {t.name for t in filtered}
        assert names == CARE_TOOLS

    def test_filter_admin_tools(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        filtered = filter_tools(tools, ADMIN_TOOLS)
        names = {t.name for t in filtered}
        assert names == ADMIN_TOOLS

    def test_filter_empty_set(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        filtered = filter_tools(tools, set())
        assert filtered == []

    def test_tools_have_descriptions(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        for t in tools:
            assert t.description, f"Tool {t.name} is missing a description"


# --- Calendar Service Tests ---


class TestCalendarService:
    """Tests for GoogleCalendarService (mocked API calls)."""

    def test_singleton_import(self):
        from app.services.calendar_service import calendar_service

        assert calendar_service is not None

    def test_not_initialised_without_config(self):
        from app.services.calendar_service import GoogleCalendarService

        svc = GoogleCalendarService()
        assert svc._initialised is False

    def test_ensure_initialised_raises_without_config(self):
        from app.services.calendar_service import GoogleCalendarService

        svc = GoogleCalendarService()
        with pytest.raises(RuntimeError, match="GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON"):
            svc._ensure_initialised()

    @patch("app.services.calendar_service.settings")
    @patch("app.services.calendar_service.build")
    @patch("app.services.calendar_service.service_account.Credentials.from_service_account_file")
    async def test_create_event(self, mock_creds, mock_build, mock_settings):
        from app.services.calendar_service import GoogleCalendarService

        mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = "/fake/path.json"
        mock_settings.GOOGLE_CALENDAR_ID = "primary"

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_insert = MagicMock()
        mock_insert.execute.return_value = {"id": "evt_123", "htmlLink": "https://cal.google.com"}
        mock_service.events.return_value.insert.return_value = mock_insert

        svc = GoogleCalendarService()
        start = datetime.now()
        end = start + timedelta(hours=1)
        event = await svc.create_event("Test Appt", start, end, description="Test")

        assert event["id"] == "evt_123"

    @patch("app.services.calendar_service.settings")
    @patch("app.services.calendar_service.build")
    @patch("app.services.calendar_service.service_account.Credentials.from_service_account_file")
    async def test_delete_event(self, mock_creds, mock_build, mock_settings):
        from app.services.calendar_service import GoogleCalendarService

        mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = "/fake/path.json"
        mock_settings.GOOGLE_CALENDAR_ID = "primary"

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_delete = MagicMock()
        mock_delete.execute.return_value = None
        mock_service.events.return_value.delete.return_value = mock_delete

        svc = GoogleCalendarService()
        result = await svc.delete_event("evt_123")
        assert result is True

    @patch("app.services.calendar_service.settings")
    @patch("app.services.calendar_service.build")
    @patch("app.services.calendar_service.service_account.Credentials.from_service_account_file")
    async def test_check_availability_free(self, mock_creds, mock_build, mock_settings):
        from app.services.calendar_service import GoogleCalendarService

        mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = "/fake/path.json"
        mock_settings.GOOGLE_CALENDAR_ID = "primary"

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_list = MagicMock()
        mock_list.execute.return_value = {"items": []}
        mock_service.events.return_value.list.return_value = mock_list

        svc = GoogleCalendarService()
        start = datetime.now()
        end = start + timedelta(hours=1)
        available = await svc.check_availability(start, end)
        assert available is True

    @patch("app.services.calendar_service.settings")
    @patch("app.services.calendar_service.build")
    @patch("app.services.calendar_service.service_account.Credentials.from_service_account_file")
    async def test_check_availability_busy(self, mock_creds, mock_build, mock_settings):
        from app.services.calendar_service import GoogleCalendarService

        mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = "/fake/path.json"
        mock_settings.GOOGLE_CALENDAR_ID = "primary"

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_list = MagicMock()
        mock_list.execute.return_value = {"items": [{"id": "existing_event"}]}
        mock_service.events.return_value.list.return_value = mock_list

        svc = GoogleCalendarService()
        start = datetime.now()
        end = start + timedelta(hours=1)
        available = await svc.check_availability(start, end)
        assert available is False

    @patch("app.services.calendar_service.settings")
    @patch("app.services.calendar_service.build")
    @patch("app.services.calendar_service.service_account.Credentials.from_service_account_info")
    async def test_inline_json_credentials(self, mock_creds, mock_build, mock_settings):
        from app.services.calendar_service import GoogleCalendarService
        import json

        fake_creds = {"type": "service_account", "project_id": "test"}
        mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = json.dumps(fake_creds)
        mock_settings.GOOGLE_CALENDAR_ID = "primary"
        mock_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        svc = GoogleCalendarService()
        svc._ensure_initialised()
        assert svc._initialised is True
        mock_creds.assert_called_once()


# --- WSMessageType Tests ---


class TestWSMessageTypePhase4:
    """Verify the new AGENT_SWITCH message type was added."""

    def test_agent_switch_exists(self):
        assert WSMessageType.AGENT_SWITCH == "agent_switch"

    def test_all_message_types_count(self):
        # Phase 3: 15, Phase 4: +1 (AGENT_SWITCH), Phase 5: +2 (AGENT_ERROR, RATE_LIMITED) = 18
        assert len(WSMessageType) == 18


# --- Appointment Model Tests ---


class TestAppointmentGoogleCalendarField:
    """Verify google_calendar_event_id column was added."""

    async def test_appointment_has_calendar_field(
        self, db_session: AsyncSession, test_patient, test_provider
    ):
        from app.models.appointment import Appointment

        appt = Appointment(
            patient_id=test_patient.id,
            provider_id=test_provider.id,
            status="booked",
            start_datetime=datetime.now() + timedelta(days=7),
            google_calendar_event_id="evt_test_123",
        )
        db_session.add(appt)
        await db_session.commit()
        await db_session.refresh(appt)
        assert appt.google_calendar_event_id == "evt_test_123"

    async def test_appointment_calendar_field_nullable(
        self, db_session: AsyncSession, test_patient, test_provider
    ):
        from app.models.appointment import Appointment

        appt = Appointment(
            patient_id=test_patient.id,
            provider_id=test_provider.id,
            status="booked",
            start_datetime=datetime.now() + timedelta(days=7),
        )
        db_session.add(appt)
        await db_session.commit()
        await db_session.refresh(appt)
        assert appt.google_calendar_event_id is None


# --- FHIR Tool Execution Tests ---


class TestFHIRToolExecution:
    """Test that wrapped FHIR tools actually execute against the DB."""

    async def test_search_patients_tool(self, db_session: AsyncSession, test_patient):
        tools = build_tools(db_session)
        search_tool = next(t for t in tools if t.name == "search_patients")
        result = await search_tool.ainvoke({"name": "John"})
        assert result["success"] is True
        assert result["data"]["total"] >= 1

    async def test_get_patient_tool(self, db_session: AsyncSession, test_patient):
        tools = build_tools(db_session)
        get_tool = next(t for t in tools if t.name == "get_patient")
        result = await get_tool.ainvoke({"patient_id": test_patient.id})
        assert result["success"] is True

    async def test_get_patient_not_found(self, db_session: AsyncSession):
        tools = build_tools(db_session)
        get_tool = next(t for t in tools if t.name == "get_patient")
        result = await get_tool.ainvoke({"patient_id": 99999})
        assert result["success"] is True  # AIFHIRService returns success with error in data
        assert "error" in result["data"]

    async def test_get_patient_encounters_tool(
        self, db_session: AsyncSession, test_patient, test_encounter
    ):
        tools = build_tools(db_session)
        enc_tool = next(t for t in tools if t.name == "get_patient_encounters")
        result = await enc_tool.ainvoke({"patient_id": test_patient.id})
        assert result["success"] is True
        assert result["data"]["total"] >= 1

    async def test_get_patient_appointments_tool(
        self, db_session: AsyncSession, test_patient, test_appointment
    ):
        tools = build_tools(db_session)
        appt_tool = next(t for t in tools if t.name == "get_patient_appointments")
        result = await appt_tool.ainvoke({"patient_id": test_patient.id})
        assert result["success"] is True
        assert result["data"]["total"] >= 1

    async def test_book_appointment_tool(self, db_session: AsyncSession, test_patient):
        tools = build_tools(db_session)
        book_tool = next(t for t in tools if t.name == "book_appointment")
        future = (datetime.now() + timedelta(days=3)).isoformat()
        result = await book_tool.ainvoke(
            {
                "patient_id": test_patient.id,
                "appointment_date": future,
                "reason": "Test booking",
                "service_type": "general",
            }
        )
        assert result["success"] is True
        assert result["data"]["status"] == "booked"

    async def test_cancel_appointment_tool(
        self, db_session: AsyncSession, test_patient, test_appointment
    ):
        tools = build_tools(db_session)
        cancel_tool = next(t for t in tools if t.name == "cancel_appointment")
        result = await cancel_tool.ainvoke(
            {"appointment_id": test_appointment.id, "reason": "Test cancel"}
        )
        assert result["success"] is True
        assert result["data"]["status"] == "cancelled"

    async def test_get_patient_observations_tool(
        self, db_session: AsyncSession, test_patient, test_observation
    ):
        tools = build_tools(db_session)
        obs_tool = next(t for t in tools if t.name == "get_patient_observations")
        result = await obs_tool.ainvoke({"patient_id": test_patient.id})
        assert result["success"] is True
        assert result["data"]["total"] >= 1


# --- Agent Graph Build Tests ---


class TestAgentGraphBuilds:
    """Test that all agent subgraphs can be compiled."""

    @patch("app.agents.intake_agent.settings")
    def test_intake_graph_builds(self, mock_settings, db_session: AsyncSession):
        from app.agents.intake_agent import build_intake_graph

        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key-for-test"
        mock_settings.GEMINI_TEMPERATURE = 0.7
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
        tools = build_tools(db_session)
        graph = build_intake_graph(tools)
        assert graph is not None

    @patch("app.agents.scheduling_agent.settings")
    def test_scheduling_graph_builds(self, mock_settings, db_session: AsyncSession):
        from app.agents.scheduling_agent import build_scheduling_graph

        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key-for-test"
        mock_settings.GEMINI_TEMPERATURE = 0.7
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
        tools = build_tools(db_session)
        graph = build_scheduling_graph(tools)
        assert graph is not None

    @patch("app.agents.care_agent.settings")
    def test_care_graph_builds(self, mock_settings, db_session: AsyncSession):
        from app.agents.care_agent import build_care_graph

        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key-for-test"
        mock_settings.GEMINI_TEMPERATURE = 0.7
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
        tools = build_tools(db_session)
        graph = build_care_graph(tools)
        assert graph is not None

    @patch("app.agents.admin_agent.settings")
    def test_admin_graph_builds(self, mock_settings, db_session: AsyncSession):
        from app.agents.admin_agent import build_admin_graph

        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GOOGLE_API_KEY = "fake-key-for-test"
        mock_settings.GEMINI_TEMPERATURE = 0.7
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
        tools = build_tools(db_session)
        graph = build_admin_graph(tools)
        assert graph is not None

    @patch("app.agents.orchestrator.settings")
    @patch("app.agents.intake_agent.settings")
    @patch("app.agents.scheduling_agent.settings")
    @patch("app.agents.care_agent.settings")
    @patch("app.agents.admin_agent.settings")
    def test_orchestrator_builds(
        self, mock_admin, mock_care, mock_sched, mock_intake, mock_orch, db_session: AsyncSession
    ):
        from app.agents.orchestrator import build_orchestrator

        for m in [mock_admin, mock_care, mock_sched, mock_intake, mock_orch]:
            m.GEMINI_MODEL = "gemini-2.0-flash"
            m.GOOGLE_API_KEY = "fake-key-for-test"
            m.GEMINI_TEMPERATURE = 0.7
            m.GEMINI_MAX_OUTPUT_TOKENS = 2048
        graph = build_orchestrator(db_session)
        assert graph is not None


# --- Config Tests ---


class TestPhase4Config:
    """Test Phase 4 config settings were added correctly."""

    def test_langgraph_recursion_limit(self):
        from app.core.config import settings

        assert settings.LANGGRAPH_RECURSION_LIMIT >= 1
        assert settings.LANGGRAPH_RECURSION_LIMIT <= 100

    def test_langgraph_max_tool_iterations(self):
        from app.core.config import settings

        assert settings.LANGGRAPH_MAX_TOOL_ITERATIONS >= 1

    def test_google_calendar_id_default(self):
        from app.core.config import settings

        assert settings.GOOGLE_CALENDAR_ID == "primary"
