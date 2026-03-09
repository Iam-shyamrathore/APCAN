"""
FHIR Patient Schemas
Reference: http://hl7.org/fhir/R4/patient.html
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.schemas.fhir import CodeableConcept, Identifier, Meta


class HumanName(BaseModel):
    """FHIR HumanName datatype"""

    use: Optional[str] = Field(None, description="usual | official | temp | nickname | anonymous")
    text: Optional[str] = Field(None, description="Full name as displayed")
    family: Optional[str] = Field(None, description="Family name (surname)")
    given: Optional[List[str]] = Field(None, description="Given names (first, middle)")
    prefix: Optional[List[str]] = Field(None, description="Title (Mr., Dr., etc.)")
    suffix: Optional[List[str]] = Field(None, description="Suffix (Jr., III, etc.)")


class ContactPoint(BaseModel):
    """FHIR ContactPoint datatype"""

    system: Optional[str] = Field(None, description="phone | email | fax | sms | etc.")
    value: Optional[str] = Field(None, description="Actual contact value")
    use: Optional[str] = Field(None, description="home | work | temp | mobile")


class Address(BaseModel):
    """FHIR Address datatype"""

    use: Optional[str] = Field(None, description="home | work | temp")
    type: Optional[str] = Field(None, description="postal | physical | both")
    text: Optional[str] = Field(None, description="Full address text")
    line: Optional[List[str]] = Field(None, description="Street address lines")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postalCode: Optional[str] = Field(None, description="Postal/ZIP code")
    country: Optional[str] = Field(None, description="Country")


class PatientContact(BaseModel):
    """FHIR Patient.contact backbone element"""

    relationship: Optional[List[CodeableConcept]] = Field(
        None, description="Relationship to patient"
    )
    name: Optional[HumanName] = Field(None, description="Contact's name")
    telecom: Optional[List[ContactPoint]] = Field(None, description="Contact details")
    address: Optional[Address] = Field(None, description="Contact address")


class PatientCreate(BaseModel):
    """Schema for creating Patient (internal API format)"""

    mrn: str = Field(..., description="Medical Record Number")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other|unknown)$")
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "USA"

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    # Insurance
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None


class PatientUpdate(BaseModel):
    """Schema for updating Patient (partial updates)"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None


class PatientResponse(BaseModel):
    """Internal API response format"""

    id: int
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: Optional[str]
    email: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    insurance_group_number: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FHIRPatient(BaseModel):
    """
    Complete FHIR R4 Patient resource
    Reference: http://hl7.org/fhir/R4/patient.html
    """

    resourceType: str = Field("Patient", description="FHIR resource type")
    id: str = Field(..., description="Logical resource ID")
    meta: Optional[Meta] = Field(None, description="Resource metadata")

    # Identifiers (MRN, insurance, SSN, etc.)
    identifier: Optional[List[Identifier]] = Field(None, description="Patient identifiers")

    # Administrative
    active: bool = Field(True, description="Whether patient record is active")

    # Demographics
    name: List[HumanName] = Field(..., description="Patient name(s)")
    telecom: Optional[List[ContactPoint]] = Field(None, description="Contact details")
    gender: str = Field(..., description="male | female | other | unknown")
    birthDate: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    address: Optional[List[Address]] = Field(None, description="Patient addresses")

    # Contacts
    contact: Optional[List[PatientContact]] = Field(None, description="Emergency contacts")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Patient",
                "id": "123",
                "meta": {"versionId": "1", "lastUpdated": "2026-01-15T10:30:00Z"},
                "identifier": [{"system": "http://hospital.example.org/mrn", "value": "MRN123456"}],
                "active": True,
                "name": [
                    {
                        "use": "official",
                        "family": "Smith",
                        "given": ["John", "Robert"],
                        "text": "John Robert Smith",
                    }
                ],
                "telecom": [
                    {"system": "phone", "value": "+1-555-123-4567", "use": "home"},
                    {"system": "email", "value": "john.smith@example.com", "use": "home"},
                ],
                "gender": "male",
                "birthDate": "1985-03-15",
                "address": [
                    {
                        "use": "home",
                        "type": "physical",
                        "line": ["123 Main St"],
                        "city": "Springfield",
                        "state": "IL",
                        "postalCode": "62701",
                        "country": "USA",
                    }
                ],
                "contact": [
                    {
                        "relationship": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                        "code": "C",
                                        "display": "Emergency Contact",
                                    }
                                ]
                            }
                        ],
                        "name": {"text": "Jane Smith"},
                        "telecom": [{"system": "phone", "value": "+1-555-987-6543"}],
                    }
                ],
            }
        }
