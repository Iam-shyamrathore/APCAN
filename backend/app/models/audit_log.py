"""
HIPAA Audit Log Model — Phase 5
Tracks all access to patient data for regulatory compliance.
Every tool execution, data retrieval, and administrative action is logged.
"""

from datetime import datetime, UTC
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """
    Immutable audit log entry for HIPAA compliance.
    Records who accessed what patient data, when, and through which tool.

    These records must never be modified or deleted.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # When the action occurred
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    # Who performed the action
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True, doc="Conversation session ID"
    )

    # What agent performed the action
    agent: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="Agent that initiated the action"
    )

    # What action was performed
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, doc="Action type: tool_call, data_access, etc."
    )
    tool_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, doc="Tool/function name if applicable"
    )
    tool_args: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, doc="Arguments passed to the tool (sanitized)"
    )

    # What patient data was accessed
    patient_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("patients.id"), nullable=True, index=True
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="FHIR resource type: Patient, Encounter, Observation, etc."
    )
    resource_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, doc="ID of the accessed resource"
    )

    # Outcome
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional context
    details: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, doc="Extra context or metadata"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"user={self.user_id}, patient={self.patient_id})>"
        )
