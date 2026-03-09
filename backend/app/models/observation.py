"""
Observation Model - Clinical measurements and findings
Industry standard: FHIR R4 Observation resource alignment  
Reference: http://hl7.org/fhir/R4/observation.html
"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.encounter import Encounter


class Observation(BaseModel):
    """
    Observation represents measurements and simple assertions about a patient
    Aligned with FHIR R4 Observation resource

    Examples: vital signs (BP, temperature), lab results, assessments
    """

    __tablename__ = "observations"

    # Patient reference (required)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Encounter reference (optional - observation may be standalone)
    encounter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Status of observation
    # FHIR ValueSet: http://hl7.org/fhir/ValueSet/observation-status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="final",
        comment="registered | preliminary | final | amended | corrected | cancelled",
    )

    # Category - type of observation
    # FHIR ValueSet: http://hl7.org/fhir/ValueSet/observation-category
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="vital-signs | laboratory | imaging | survey | etc.",
    )

    # Code - what was measured
    # Preferred: LOINC codes (http://loinc.org)
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="LOINC code (e.g., '85354-9' for Blood Pressure)",
    )

    # Human-readable display
    display: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable name (e.g., 'Blood Pressure', 'Body Temperature')",
    )

    # Quantitative value
    value_quantity: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Numerical value (e.g., 120 for systolic BP)"
    )

    # Unit of measurement
    value_unit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Unit (e.g., 'mmHg', 'kg', 'celsius')"
    )

    # String value (for non-numeric observations)
    value_string: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Text value (e.g., 'Positive', 'Negative', 'Moderate')"
    )

    # Reference range - low bound
    reference_range_low: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Lower bound of normal range"
    )

    # Reference range - high bound
    reference_range_high: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Upper bound of normal range"
    )

    # When observation was made (clinically relevant time)
    effective_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True, comment="When observation was taken"
    )

    # When observation was issued/reported
    issued: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When observation result was released"
    )

    # Interpretation (e.g., high, low, normal)
    interpretation: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="normal | high | low | critical | etc."
    )

    # Additional notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Comments about the observation"
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="observations")
    encounter: Mapped[Optional["Encounter"]] = relationship(
        "Encounter", back_populates="observations"
    )

    def __repr__(self) -> str:
        return f"<Observation(id={self.id}, patient_id={self.patient_id}, code={self.code}, value={self.value_quantity} {self.value_unit})>"
