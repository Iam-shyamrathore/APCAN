"""
Tests for AI FHIR Service - tool execution for Gemini function calling.
"""

import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.appointment import Appointment
from app.models.observation import Observation
from app.services.ai_fhir_service import AIFHIRService


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def ai_fhir(db_session: AsyncSession):
    return AIFHIRService(db_session)


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    user = User(
        email="patient@test.com",
        hashed_password="fakehash",
        full_name="Test User",
        role="patient",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_patient(db_session: AsyncSession, sample_user):
    patient = Patient(
        user_id=sample_user.id,
        given_name="Alice",
        family_name="Smith",
        birth_date=date(1990, 5, 15),
        gender="female",
        phone="+1-555-0101",
        mrn="MRN-001",
        city="Boston",
        state="MA",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def sample_provider(db_session: AsyncSession):
    user = User(
        email="dr@test.com",
        hashed_password="fakehash",
        full_name="Dr Jones",
        role="clinician",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_encounter(db_session: AsyncSession, sample_patient, sample_provider):
    encounter = Encounter(
        patient_id=sample_patient.id,
        provider_id=sample_provider.id,
        encounter_class="outpatient",
        status="finished",
        period_start=datetime.now() - timedelta(days=3),
        period_end=datetime.now() - timedelta(days=3, hours=-1),
        reason_code="R51",
        reason_display="Headache",
    )
    db_session.add(encounter)
    await db_session.commit()
    await db_session.refresh(encounter)
    return encounter


@pytest_asyncio.fixture
async def sample_appointment(db_session: AsyncSession, sample_patient, sample_provider):
    appt = Appointment(
        patient_id=sample_patient.id,
        provider_id=sample_provider.id,
        status="booked",
        appointment_type="ROUTINE",
        start_datetime=datetime.now() + timedelta(days=7),
        duration_minutes=30,
        comment="Annual checkup",
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest_asyncio.fixture
async def sample_observation(db_session: AsyncSession, sample_patient, sample_encounter):
    obs = Observation(
        patient_id=sample_patient.id,
        encounter_id=sample_encounter.id,
        status="final",
        category="vital-signs",
        code="8480-6",
        display="Systolic blood pressure",
        effective_datetime=datetime.now() - timedelta(days=3),
        value_quantity=120.0,
        value_unit="mmHg",
    )
    db_session.add(obs)
    await db_session.commit()
    await db_session.refresh(obs)
    return obs


class TestAIFHIRService:
    """Tests for AI FHIR tool execution."""

    async def test_execute_unknown_tool(self, ai_fhir):
        result = await ai_fhir.execute_tool("nonexistent_tool", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    async def test_search_patients_by_name(self, ai_fhir, sample_patient):
        result = await ai_fhir.execute_tool("search_patients", {"name": "Alice"})
        assert result["success"] is True
        assert result["data"]["total"] >= 1
        assert result["data"]["patients"][0]["name"] == "Alice Smith"

    async def test_search_patients_by_mrn(self, ai_fhir, sample_patient):
        result = await ai_fhir.execute_tool("search_patients", {"mrn": "MRN-001"})
        assert result["success"] is True
        assert result["data"]["total"] == 1

    async def test_search_patients_no_results(self, ai_fhir):
        result = await ai_fhir.execute_tool("search_patients", {"name": "Nonexistent"})
        assert result["success"] is True
        assert result["data"]["total"] == 0

    async def test_get_patient(self, ai_fhir, sample_patient):
        result = await ai_fhir.execute_tool("get_patient", {"patient_id": sample_patient.id})
        assert result["success"] is True
        # FHIR response should have resourceType
        assert result["data"].get("resourceType") == "Patient"

    async def test_get_patient_not_found(self, ai_fhir):
        result = await ai_fhir.execute_tool("get_patient", {"patient_id": 99999})
        assert result["success"] is True
        assert "error" in result["data"]

    async def test_get_patient_encounters(self, ai_fhir, sample_patient, sample_encounter):
        result = await ai_fhir.execute_tool(
            "get_patient_encounters", {"patient_id": sample_patient.id}
        )
        assert result["success"] is True
        assert result["data"]["total"] >= 1
        assert result["data"]["encounters"][0]["status"] == "finished"

    async def test_get_patient_encounters_with_status_filter(
        self, ai_fhir, sample_patient, sample_encounter
    ):
        result = await ai_fhir.execute_tool(
            "get_patient_encounters",
            {"patient_id": sample_patient.id, "status": "planned"},
        )
        assert result["success"] is True
        assert result["data"]["total"] == 0

    async def test_get_patient_appointments(self, ai_fhir, sample_patient, sample_appointment):
        result = await ai_fhir.execute_tool(
            "get_patient_appointments", {"patient_id": sample_patient.id}
        )
        assert result["success"] is True
        assert result["data"]["total"] >= 1
        assert result["data"]["appointments"][0]["status"] == "booked"

    async def test_book_appointment(self, ai_fhir, sample_patient):
        future_date = (datetime.now() + timedelta(days=14)).isoformat()
        result = await ai_fhir.execute_tool(
            "book_appointment",
            {
                "patient_id": sample_patient.id,
                "appointment_date": future_date,
                "reason": "Follow-up visit",
                "service_type": "general",
            },
        )
        assert result["success"] is True
        assert result["data"]["status"] == "booked"
        assert result["data"]["appointment_id"] is not None

    async def test_book_appointment_invalid_patient(self, ai_fhir):
        result = await ai_fhir.execute_tool(
            "book_appointment",
            {
                "patient_id": 99999,
                "appointment_date": datetime.now().isoformat(),
                "reason": "Test",
            },
        )
        assert result["success"] is True
        assert "error" in result["data"]

    async def test_book_appointment_invalid_date(self, ai_fhir, sample_patient):
        result = await ai_fhir.execute_tool(
            "book_appointment",
            {
                "patient_id": sample_patient.id,
                "appointment_date": "not-a-date",
                "reason": "Test",
            },
        )
        assert result["success"] is True
        assert "error" in result["data"]

    async def test_cancel_appointment(self, ai_fhir, sample_appointment):
        result = await ai_fhir.execute_tool(
            "cancel_appointment",
            {"appointment_id": sample_appointment.id, "reason": "Patient request"},
        )
        assert result["success"] is True
        assert result["data"]["status"] == "cancelled"

    async def test_cancel_appointment_not_found(self, ai_fhir):
        result = await ai_fhir.execute_tool("cancel_appointment", {"appointment_id": 99999})
        assert result["success"] is True
        assert "error" in result["data"]

    async def test_cancel_already_cancelled(self, ai_fhir, sample_appointment, db_session):
        sample_appointment.status = "cancelled"
        await db_session.commit()

        result = await ai_fhir.execute_tool(
            "cancel_appointment", {"appointment_id": sample_appointment.id}
        )
        assert result["success"] is True
        assert "already cancelled" in result["data"]["error"]

    async def test_get_patient_observations(self, ai_fhir, sample_patient, sample_observation):
        result = await ai_fhir.execute_tool(
            "get_patient_observations", {"patient_id": sample_patient.id}
        )
        assert result["success"] is True
        assert result["data"]["total"] >= 1
        assert result["data"]["observations"][0]["code"] == "8480-6"

    async def test_get_patient_observations_with_code_filter(
        self, ai_fhir, sample_patient, sample_observation
    ):
        result = await ai_fhir.execute_tool(
            "get_patient_observations",
            {"patient_id": sample_patient.id, "code": "8480-6"},
        )
        assert result["success"] is True
        assert result["data"]["total"] >= 1

    async def test_get_patient_observations_no_match(
        self, ai_fhir, sample_patient, sample_observation
    ):
        result = await ai_fhir.execute_tool(
            "get_patient_observations",
            {"patient_id": sample_patient.id, "code": "99999-9"},
        )
        assert result["success"] is True
        assert result["data"]["total"] == 0
