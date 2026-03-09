"""
Encounter Model - Clinical visit/admission record
Industry standard: FHIR R4 Encounter resource alignment
Reference: http://hl7.org/fhir/R4/encounter.html
"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.observation import Observation


class Encounter(BaseModel):
    """
    Encounter represents an interaction between a patient and healthcare provider(s)
    Aligned with FHIR R4 Encounter resource
    
    Examples: office visit, emergency room visit, hospital admission
    """
    __tablename__ = "encounters"
    
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
    
    # Encounter class (classification of setting)
    # FHIR ValueSet: http://hl7.org/fhir/ValueSet/v3-ActEncounterCode
    encounter_class: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="inpatient | outpatient | ambulatory | emergency | home | field | virtual"
    )
    
    # Status of encounter
    # FHIR ValueSet: http://hl7.org/fhir/ValueSet/encounter-status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planned",
        comment="planned | arrived | triaged | in-progress | onleave | finished | cancelled"
    )
    
    # Time period of encounter
    period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Start time of encounter"
    )
    
    period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="End time of encounter"
    )
    
    # Reason for encounter (coded)
    reason_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="SNOMED CT or ICD-10 code for reason"
    )
    
    # Reason for encounter (human-readable)
    reason_display: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable reason (e.g., 'Annual physical', 'Chest pain')"
    )
    
    # Additional notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the encounter"
    )
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    provider: Mapped[Optional["User"]] = relationship("User", back_populates="encounters")
    observations: Mapped[list["Observation"]] = relationship(
        "Observation",
        back_populates="encounter",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Encounter(id={self.id}, patient_id={self.patient_id}, class={self.encounter_class}, status={self.status})>"
