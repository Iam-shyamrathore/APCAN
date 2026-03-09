"""
LangGraph Tool Definitions — wraps FHIR + Calendar operations as LangChain tools.

Each tool is a plain async function decorated with @tool.  They are instantiated
via ``build_tools(db)`` which closes over the database session so every tool
invocation shares the same transaction context.
"""

import logging
from datetime import datetime, timedelta

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_fhir_service import AIFHIRService
from app.services.calendar_service import calendar_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool factory — returns a list of LangChain @tool functions bound to a db
# ---------------------------------------------------------------------------


def build_tools(db: AsyncSession) -> list:
    """
    Build the complete set of LangGraph tools for the current request.

    The returned tools close over *db* so that every invocation uses the same
    async session (and therefore the same transaction).
    """
    fhir = AIFHIRService(db)

    # -- FHIR Tools (wrap existing service) --------------------------------

    @tool
    async def search_patients(
        name: str | None = None,
        mrn: str | None = None,
        birth_date: str | None = None,
    ) -> dict:
        """Search for patients by name, MRN, or birth date. Use when the user asks to find a patient."""
        return await fhir.execute_tool(
            "search_patients",
            {"name": name, "mrn": mrn, "birth_date": birth_date},
        )

    @tool
    async def get_patient(patient_id: int) -> dict:
        """Get detailed information about a specific patient by their ID."""
        return await fhir.execute_tool("get_patient", {"patient_id": patient_id})

    @tool
    async def get_patient_encounters(
        patient_id: int,
        status: str | None = None,
    ) -> dict:
        """Get a patient's clinical encounters (visits). Use when asked about visit history."""
        return await fhir.execute_tool(
            "get_patient_encounters",
            {"patient_id": patient_id, "status": status},
        )

    @tool
    async def get_patient_appointments(
        patient_id: int,
        status: str | None = None,
    ) -> dict:
        """Get a patient's appointments. Use when asked about upcoming or past appointments."""
        return await fhir.execute_tool(
            "get_patient_appointments",
            {"patient_id": patient_id, "status": status},
        )

    @tool
    async def book_appointment(
        patient_id: int,
        appointment_date: str,
        reason: str,
        service_type: str = "general",
    ) -> dict:
        """Book a new appointment for a patient. Use when the user wants to schedule a visit."""
        return await fhir.execute_tool(
            "book_appointment",
            {
                "patient_id": patient_id,
                "appointment_date": appointment_date,
                "reason": reason,
                "service_type": service_type,
            },
        )

    @tool
    async def cancel_appointment(
        appointment_id: int,
        reason: str | None = None,
    ) -> dict:
        """Cancel an existing appointment. Use when the user wants to cancel a scheduled visit."""
        return await fhir.execute_tool(
            "cancel_appointment",
            {"appointment_id": appointment_id, "reason": reason},
        )

    @tool
    async def get_patient_observations(
        patient_id: int,
        code: str | None = None,
    ) -> dict:
        """Get a patient's clinical observations (vitals, lab results). Use for vitals or test results."""
        return await fhir.execute_tool(
            "get_patient_observations",
            {"patient_id": patient_id, "code": code},
        )

    # -- Calendar Tools (new in Phase 4) -----------------------------------

    @tool
    async def check_provider_availability(
        start_time: str,
        end_time: str | None = None,
        calendar_id: str | None = None,
    ) -> dict:
        """Check if a time slot is available on the provider's calendar. start_time in ISO 8601."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time) if end_time else start + timedelta(minutes=30)
            available = await calendar_service.check_availability(
                start=start, end=end, calendar_id=calendar_id
            )
            return {
                "success": True,
                "data": {
                    "available": available,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                },
            }
        except Exception as e:
            logger.exception("check_provider_availability failed")
            return {"success": False, "error": str(e)}

    @tool
    async def create_calendar_event(
        summary: str,
        start_time: str,
        end_time: str | None = None,
        description: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str | None = None,
    ) -> dict:
        """Create a Google Calendar event for an appointment. start_time/end_time in ISO 8601."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time) if end_time else start + timedelta(minutes=30)
            event = await calendar_service.create_event(
                summary=summary,
                start=start,
                end=end,
                description=description,
                attendees=attendees,
                calendar_id=calendar_id,
            )
            return {
                "success": True,
                "data": {
                    "event_id": event.get("id"),
                    "html_link": event.get("htmlLink"),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                },
            }
        except Exception as e:
            logger.exception("create_calendar_event failed")
            return {"success": False, "error": str(e)}

    @tool
    async def cancel_calendar_event(
        event_id: str,
        calendar_id: str | None = None,
    ) -> dict:
        """Cancel (delete) a Google Calendar event by its event ID."""
        try:
            await calendar_service.delete_event(event_id=event_id, calendar_id=calendar_id)
            return {"success": True, "data": {"event_id": event_id, "status": "cancelled"}}
        except Exception as e:
            logger.exception("cancel_calendar_event failed")
            return {"success": False, "error": str(e)}

    return [
        # FHIR tools (7)
        search_patients,
        get_patient,
        get_patient_encounters,
        get_patient_appointments,
        book_appointment,
        cancel_appointment,
        get_patient_observations,
        # Calendar tools (3)
        check_provider_availability,
        create_calendar_event,
        cancel_calendar_event,
    ]


# ---------------------------------------------------------------------------
# Tool subsets for specialised agents
# ---------------------------------------------------------------------------

# Tool name sets per agent — used by agent subgraphs to filter the full list
INTAKE_TOOLS = {"search_patients", "get_patient"}
SCHEDULING_TOOLS = {
    "get_patient_appointments",
    "book_appointment",
    "cancel_appointment",
    "check_provider_availability",
    "create_calendar_event",
    "cancel_calendar_event",
}
CARE_TOOLS = {"get_patient", "get_patient_encounters", "get_patient_observations"}
ADMIN_TOOLS = {"search_patients", "get_patient", "get_patient_encounters"}


def filter_tools(all_tools: list, names: set[str]) -> list:
    """Return only tools whose names are in *names*."""
    return [t for t in all_tools if t.name in names]
