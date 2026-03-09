"""
Appointment Model - Scheduled patient visit
Industry standard: FHIR R4 Appointment resource alignment
Reference: http://hl7.org/fhir/R4/appointment.html
"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient import Patient


class Appointment(BaseModel):
    """
    Appointment represents a booking of healthcare service for a patient
    Aligned with FHIR R4 Appointment resource
    
    Used by voice AI agents for autonomous scheduling
    """
    __tablename__ = "appointments"
    
    # Patient reference (required)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Provider/practitioner reference (optional)
    provider_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Status of appointment
    # FHIR ValueSet: http://hl7.org/fhir/ValueSet/appointmentstatus
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="proposed",
        index=True,
        comment="proposed | pending | booked | arrived | fulfilled | cancelled | noshow"
    )
    
    # Type of appointment
    appointment_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="ROUTINE | URGENT | EMERGENCY | FOLLOWUP | etc."
    )
    
    # Service category
    service_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="General Practice | Specialist | Therapy | etc."
    )
    
    # Start datetime of appointment
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When appointment is scheduled to start"
    )
    
    # End datetime of appointment
    end_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When appointment is scheduled to end"
    )
    
    # Duration in minutes
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected duration (optional if end_datetime provided)"
    )
    
    # Comment/Instructions
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional instructions (e.g., 'Bring insurance card', 'Fasting required')"
    )
    
    # Cancellation reason (if cancelled)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for cancellation if status is cancelled"
    )
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    provider: Mapped[Optional["User"]] = relationship("User", back_populates="appointments")
    
    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, start={self.start_datetime}, status={self.status})>"
