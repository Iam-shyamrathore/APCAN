"""
HIPAA Audit Service — Phase 5
Provides methods to log and query audit trail entries.
All tool executions and patient data access must be logged here.
"""

import logging
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Map tool names to the FHIR resource type they access
_TOOL_RESOURCE_MAP: dict[str, str] = {
    "search_patients": "Patient",
    "get_patient": "Patient",
    "get_patient_encounters": "Encounter",
    "get_patient_appointments": "Appointment",
    "book_appointment": "Appointment",
    "cancel_appointment": "Appointment",
    "get_patient_observations": "Observation",
    "check_provider_availability": "Calendar",
    "create_calendar_event": "Calendar",
    "cancel_calendar_event": "Calendar",
}


class AuditService:
    """Logs HIPAA-compliant audit entries to the database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log_tool_call(
        self,
        tool_name: str,
        tool_args: dict | None = None,
        success: bool = True,
        error_message: str | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        agent: str | None = None,
        patient_id: int | None = None,
        resource_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Log a single tool/function call."""
        # Extract patient_id from args if not provided explicitly
        if patient_id is None and tool_args:
            pid = tool_args.get("patient_id")
            if pid is not None:
                patient_id = int(pid)

        entry = AuditLog(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            session_id=session_id,
            agent=agent,
            action="tool_call",
            tool_name=tool_name,
            tool_args=_sanitize_args(tool_args) if tool_args else None,
            patient_id=patient_id,
            resource_type=_TOOL_RESOURCE_MAP.get(tool_name),
            resource_id=resource_id,
            success=success,
            error_message=error_message,
            details=details,
        )
        self.db.add(entry)
        try:
            await self.db.flush()
        except Exception:
            logger.warning("Failed to flush audit log entry for %s", tool_name)
        return entry

    async def log_data_access(
        self,
        resource_type: str,
        resource_id: int | None = None,
        patient_id: int | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        agent: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Log a data access event (read, search, etc.)."""
        entry = AuditLog(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            session_id=session_id,
            agent=agent,
            action="data_access",
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            success=True,
            details=details,
        )
        self.db.add(entry)
        try:
            await self.db.flush()
        except Exception:
            logger.warning("Failed to flush audit log for %s access", resource_type)
        return entry

    async def get_logs(
        self,
        patient_id: int | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Query audit logs with optional filters."""
        query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

        if patient_id is not None:
            query = query.where(AuditLog.patient_id == patient_id)
        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if session_id is not None:
            query = query.where(AuditLog.session_id == session_id)
        if action is not None:
            query = query.where(AuditLog.action == action)

        result = await self.db.execute(query)
        return list(result.scalars().all())


def _sanitize_args(args: dict) -> dict:
    """Remove sensitive fields from tool arguments before logging."""
    sanitized = dict(args)
    # Strip any accidental credential or token data
    for key in ("password", "token", "secret", "api_key", "credentials"):
        sanitized.pop(key, None)
    return sanitized
