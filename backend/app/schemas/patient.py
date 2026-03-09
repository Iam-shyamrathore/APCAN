"""
Patient Pydantic Schemas
Industry standard: FHIR-aligned validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime


class PatientBase(BaseModel):
    """Base patient schema"""
    given_name: str = Field(..., min_length=1, max_length=100)
    family_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    gender: Optional[str] = Field(None, pattern="^(male|female|other|unknown)$")
    phone: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for patient creation"""
    user_id: int


class PatientUpdate(BaseModel):
    """Schema for patient update"""
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    phone: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    mrn: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    created_at: datetime
