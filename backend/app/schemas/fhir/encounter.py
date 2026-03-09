"""
FHIR Encounter Schemas
Reference: http://hl7.org/fhir/R4/encounter.html
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.fhir import CodeableConcept, Period, Reference, Meta


class EncounterCreate(BaseModel):
    """Create Encounter request"""
    patient_id: int = Field(..., description="Patient reference (internal ID)")
    provider_id: Optional[int] = Field(None, description="Provider/practitioner reference (internal ID)")
    encounter_class: str = Field(..., description="inpatient | outpatient | ambulatory | emergency | home | field | virtual")
    status: str = Field(default="planned", description="planned | arrived | triaged | in-progress | onleave | finished | cancelled")
    period_start: Optional[datetime] = Field(None, description="Start time of encounter")
    period_end: Optional[datetime] = Field(None, description="End time of encounter")
    reason_code: Optional[str] = Field(None, description="SNOMED CT or ICD-10 code for reason")
    reason_display: Optional[str] = Field(None, description="Human-readable reason")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": 1,
                "provider_id": 2,
                "encounter_class": "outpatient",
                "status": "planned",
                "period_start": "2026-03-15T10:00:00Z",
                "reason_display": "Annual physical examination"
            }
        }


class EncounterUpdate(BaseModel):
    """Update Encounter request"""
    provider_id: Optional[int] = None
    encounter_class: Optional[str] = None
    status: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    reason_code: Optional[str] = None
    reason_display: Optional[str] = None
    notes: Optional[str] = None


class EncounterResponse(BaseModel):
    """Internal Encounter response (Non-FHIR)"""
    id: int
    patient_id: int
    provider_id: Optional[int]
    encounter_class: str
    status: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    reason_code: Optional[str]
    reason_display: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FHIREncounter(BaseModel):
    """
    FHIR R4 Encounter resource
    Full FHIR-compliant response format
    """
    resourceType: str = Field(default="Encounter", const=True)
    id: str = Field(..., description="Logical id of this artifact")
    meta: Optional[Meta] = Field(None, description="Metadata about the resource")
    
    status: str = Field(..., description="planned | arrived | triaged | in-progress | onleave | finished | cancelled")
    class_: CodeableConcept = Field(..., alias="class", description="Classification of patient encounter")
    
    subject: Reference = Field(..., description="The patient present at the encounter")
    participant: Optional[List[dict]] = Field(None, description="List of participants (providers)")
    
    period: Optional[Period] = Field(None, description="The start and end time of the encounter")
    reasonCode: Optional[List[CodeableConcept]] = Field(None, description="Coded reason the encounter takes place")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "resourceType": "Encounter",
                "id": "1",
                "meta": {
                    "versionId": "1",
                    "lastUpdated": "2026-03-09T10:30:00Z"
                },
                "status": "planned",
                "class": {
                    "code": "AMB",
                    "display": "ambulatory"
                },
                "subject": {
                    "reference": "Patient/1",
                    "display": "John Doe"
                },
                "period": {
                    "start": "2026-03-15T10:00:00Z"
                },
                "reasonCode": [
                    {
                        "code": "390906007",
                        "display": "Annual physical examination",
                        "system": "http://snomed.info/sct"
                    }
                ]
            }
        }
