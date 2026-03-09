"""
FHIR Appointment Schemas
Reference: http://hl7.org/fhir/R4/appointment.html
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.fhir import CodeableConcept, Meta


class AppointmentCreate(BaseModel):
    """Create Appointment request"""

    patient_id: int = Field(..., description="Patient reference (internal ID)")
    provider_id: Optional[int] = Field(
        None, description="Provider/practitioner reference (internal ID)"
    )
    status: str = Field(
        default="proposed",
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow",
    )
    appointment_type: Optional[str] = Field(
        None, description="ROUTINE | URGENT | EMERGENCY | FOLLOWUP"
    )
    service_category: Optional[str] = Field(
        None, description="General Practice | Specialist | Therapy"
    )
    start_datetime: datetime = Field(..., description="When appointment starts")
    end_datetime: Optional[datetime] = Field(None, description="When appointment ends")
    duration_minutes: Optional[int] = Field(None, description="Expected duration in minutes")
    comment: Optional[str] = Field(None, description="Additional instructions or comments")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": 1,
                "provider_id": 2,
                "status": "booked",
                "appointment_type": "ROUTINE",
                "service_category": "General Practice",
                "start_datetime": "2026-03-20T14:00:00Z",
                "duration_minutes": 30,
                "comment": "Bring insurance card",
            }
        }


class AppointmentUpdate(BaseModel):
    """Update Appointment request"""

    provider_id: Optional[int] = None
    status: Optional[str] = None
    appointment_type: Optional[str] = None
    service_category: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    comment: Optional[str] = None
    cancellation_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Internal Appointment response (Non-FHIR)"""

    id: int
    patient_id: int
    provider_id: Optional[int]
    status: str
    appointment_type: Optional[str]
    service_category: Optional[str]
    start_datetime: datetime
    end_datetime: Optional[datetime]
    duration_minutes: Optional[int]
    comment: Optional[str]
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FHIRAppointment(BaseModel):
    """
    FHIR R4 Appointment resource
    Full FHIR-compliant response format
    """

    resourceType: str = Field(default="Appointment", const=True)
    id: str = Field(..., description="Logical id of this artifact")
    meta: Optional[Meta] = Field(None, description="Metadata about the resource")

    status: str = Field(
        ..., description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow"
    )
    appointmentType: Optional[CodeableConcept] = Field(None, description="The style of appointment")
    serviceCategory: Optional[List[CodeableConcept]] = Field(
        None, description="Category of service"
    )

    start: datetime = Field(..., description="When appointment is to take place")
    end: Optional[datetime] = Field(None, description="When appointment is to conclude")
    minutesDuration: Optional[int] = Field(None, description="Duration in minutes")

    participant: List[dict] = Field(..., description="Participants involved (patient, provider)")
    comment: Optional[str] = Field(None, description="Additional comments")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Appointment",
                "id": "1",
                "meta": {"versionId": "1", "lastUpdated": "2026-03-09T10:30:00Z"},
                "status": "booked",
                "appointmentType": {"code": "ROUTINE", "display": "Routine appointment"},
                "serviceCategory": [{"code": "gp", "display": "General Practice"}],
                "start": "2026-03-20T14:00:00Z",
                "minutesDuration": 30,
                "participant": [
                    {
                        "actor": {"reference": "Patient/1", "display": "John Doe"},
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": {"reference": "Practitioner/2", "display": "Dr. Jane Smith"},
                        "required": "required",
                        "status": "accepted",
                    },
                ],
                "comment": "Bring insurance card",
            }
        }
