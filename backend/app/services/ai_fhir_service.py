"""
AI FHIR Service - Executes FHIR tool calls requested by the Gemini AI.
Bridges the gap between AI function calling and the FHIR mapper / database.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.appointment import Appointment
from app.models.observation import Observation
from app.services.fhir_mapper import FHIRMapper

logger = logging.getLogger(__name__)

# Maps AI tool names → handler methods
TOOL_REGISTRY: dict[str, str] = {
    "search_patients": "_search_patients",
    "get_patient": "_get_patient",
    "get_patient_encounters": "_get_patient_encounters",
    "get_patient_appointments": "_get_patient_appointments",
    "book_appointment": "_book_appointment",
    "cancel_appointment": "_cancel_appointment",
    "get_patient_observations": "_get_patient_observations",
}


class AIFHIRService:
    """
    Executes AI-requested FHIR tool calls against the database.
    Each method returns a dict suitable for sending back to Gemini as a tool result.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        """
        Route a tool call to the appropriate handler.

        Args:
            tool_name: Name from Gemini function_call
            args: Arguments dict from function_call

        Returns:
            {"success": True/False, "data": ...} or {"success": False, "error": ...}
        """
        handler_name = TOOL_REGISTRY.get(tool_name)
        if not handler_name:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        handler = getattr(self, handler_name)
        try:
            result = await handler(**args)
            return {"success": True, "data": result}
        except Exception as e:
            logger.exception("Tool execution failed: %s(%s)", tool_name, args)
            return {"success": False, "error": str(e)}

    # --- Tool Implementations ---

    async def _search_patients(
        self,
        name: str | None = None,
        mrn: str | None = None,
        birth_date: str | None = None,
    ) -> dict:
        """Search patients by name, MRN, or birth date."""
        query = select(Patient).where(Patient.is_deleted.is_(False))

        if mrn:
            query = query.where(Patient.mrn == mrn)
        if name:
            name_filter = f"%{name}%"
            query = query.where(
                (Patient.given_name.ilike(name_filter)) | (Patient.family_name.ilike(name_filter))
            )
        if birth_date:
            query = query.where(Patient.birth_date == birth_date)

        query = query.limit(10)
        result = await self.db.execute(query)
        patients = result.scalars().all()

        return {
            "total": len(patients),
            "patients": [
                {
                    "id": p.id,
                    "name": f"{p.given_name} {p.family_name}",
                    "mrn": p.mrn,
                    "birth_date": str(p.birth_date) if p.birth_date else None,
                    "gender": p.gender,
                }
                for p in patients
            ],
        }

    async def _get_patient(self, patient_id: int) -> dict:
        """Get detailed patient info by ID."""
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.is_deleted:
            return {"error": f"Patient {patient_id} not found"}

        fhir_patient = FHIRMapper.patient_to_fhir(patient)
        return fhir_patient.model_dump(mode="json", exclude_none=True)

    async def _get_patient_encounters(
        self,
        patient_id: int,
        status: str | None = None,
    ) -> dict:
        """Get encounters for a patient."""
        query = (
            select(Encounter)
            .options(selectinload(Encounter.patient))
            .where(Encounter.patient_id == patient_id)
            .where(Encounter.is_deleted.is_(False))
            .order_by(Encounter.period_start.desc())
            .limit(20)
        )
        if status:
            query = query.where(Encounter.status == status)

        result = await self.db.execute(query)
        encounters = result.scalars().all()

        return {
            "total": len(encounters),
            "encounters": [
                {
                    "id": e.id,
                    "status": e.status,
                    "class": e.encounter_class,
                    "start": str(e.period_start) if e.period_start else None,
                    "end": str(e.period_end) if e.period_end else None,
                    "reason": e.reason_display or e.reason_code,
                }
                for e in encounters
            ],
        }

    async def _get_patient_appointments(
        self,
        patient_id: int,
        status: str | None = None,
    ) -> dict:
        """Get appointments for a patient."""
        query = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .where(Appointment.is_deleted.is_(False))
            .order_by(Appointment.start_datetime.desc())
            .limit(20)
        )
        if status:
            query = query.where(Appointment.status == status)

        result = await self.db.execute(query)
        appointments = result.scalars().all()

        return {
            "total": len(appointments),
            "appointments": [
                {
                    "id": a.id,
                    "status": a.status,
                    "date": str(a.start_datetime) if a.start_datetime else None,
                    "duration": a.duration_minutes,
                    "type": a.appointment_type,
                    "service_category": a.service_category,
                }
                for a in appointments
            ],
        }

    async def _book_appointment(
        self,
        patient_id: int,
        appointment_date: str,
        reason: str,
        service_type: str = "general",
    ) -> dict:
        """Book a new appointment."""
        # Verify patient exists
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.is_deleted:
            return {"error": f"Patient {patient_id} not found"}

        try:
            parsed_date = datetime.fromisoformat(appointment_date)
        except ValueError:
            return {"error": f"Invalid date format: {appointment_date}. Use ISO 8601."}

        appointment = Appointment(
            patient_id=patient_id,
            start_datetime=parsed_date,
            status="booked",
            comment=reason,
            appointment_type=service_type,
            duration_minutes=30,
        )
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        return {
            "appointment_id": appointment.id,
            "status": "booked",
            "date": str(appointment.start_datetime),
            "reason": appointment.comment,
            "message": f"Appointment booked for {patient.given_name} {patient.family_name} "
            f"on {parsed_date.strftime('%B %d, %Y at %I:%M %p')}.",
        }

    async def _cancel_appointment(
        self,
        appointment_id: int,
        reason: str | None = None,
    ) -> dict:
        """Cancel an appointment."""
        appointment = await self.db.get(Appointment, appointment_id)
        if not appointment or appointment.is_deleted:
            return {"error": f"Appointment {appointment_id} not found"}

        if appointment.status == "cancelled":
            return {"error": "Appointment is already cancelled"}

        appointment.status = "cancelled"
        appointment.cancellation_reason = reason or "Cancelled by voice assistant"
        await self.db.commit()

        return {
            "appointment_id": appointment.id,
            "status": "cancelled",
            "message": "Appointment has been cancelled successfully.",
        }

    async def _get_patient_observations(
        self,
        patient_id: int,
        code: str | None = None,
    ) -> dict:
        """Get clinical observations (vitals, lab results) for a patient."""
        query = (
            select(Observation)
            .where(Observation.patient_id == patient_id)
            .where(Observation.is_deleted.is_(False))
            .order_by(Observation.effective_datetime.desc())
            .limit(20)
        )
        if code:
            query = query.where(Observation.code == code)

        result = await self.db.execute(query)
        observations = result.scalars().all()

        return {
            "total": len(observations),
            "observations": [
                {
                    "id": o.id,
                    "code": o.code,
                    "display": o.display,
                    "value": o.value_quantity,
                    "unit": o.value_unit,
                    "date": str(o.effective_datetime) if o.effective_datetime else None,
                    "status": o.status,
                }
                for o in observations
            ],
        }
