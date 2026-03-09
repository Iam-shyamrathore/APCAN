"""
Patient Model - FHIR-aligned patient data
Industry standard: FHIR R4 specification alignment
"""

from datetime import date
from sqlalchemy import String, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.encounter import Encounter
    from app.models.appointment import Appointment
    from app.models.observation import Observation


class Patient(BaseModel):
    """
    Patient model aligned with FHIR Patient resource
    https://www.hl7.org/fhir/patient.html
    """

    __tablename__ = "patients"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True
    )

    # FHIR Patient.name fields
    given_name: Mapped[str] = mapped_column(String(100), nullable=False, doc="First name")
    family_name: Mapped[str] = mapped_column(String(100), nullable=False, doc="Last name")

    # FHIR Patient.birthDate
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)

    # FHIR Patient.gender (administrative gender)
    gender: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, doc="Administrative gender: male, female, other, unknown"
    )

    # FHIR Patient.telecom
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # FHIR Patient.address
    address_line: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # FHIR Patient.identifier (Medical Record Number)
    mrn: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
        doc="Medical Record Number - unique patient identifier",
    )

    # Additional clinical fields
    allergies: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="JSON array of allergies"
    )

    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="patient")
    encounters: Mapped[list["Encounter"]] = relationship(
        "Encounter", back_populates="patient", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="patient", cascade="all, delete-orphan"
    )
    observations: Mapped[list["Observation"]] = relationship(
        "Observation", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name={self.given_name} {self.family_name}, mrn={self.mrn})>"
