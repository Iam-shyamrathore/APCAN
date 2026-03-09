"""
User Model - Authentication and Authorization
Industry standard: RBAC with enum roles
"""

from enum import Enum as PyEnum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.appointment import Appointment


class UserRole(str, PyEnum):
    """User roles for RBAC"""

    ADMIN = "admin"
    CLINICIAN = "clinician"
    PATIENT = "patient"
    AGENT = "agent"  # For AI agent service accounts


class User(BaseModel):
    """User model for authentication"""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.PATIENT, nullable=False, doc="User role for RBAC"
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships (as provider/clinician)
    encounters: Mapped[list["Encounter"]] = relationship(
        "Encounter", back_populates="provider", foreign_keys="[Encounter.provider_id]"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="provider", foreign_keys="[Appointment.provider_id]"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
