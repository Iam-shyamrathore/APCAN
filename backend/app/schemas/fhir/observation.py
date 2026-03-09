"""
FHIR Observation Schemas
Reference: http://hl7.org/fhir/R4/observation.html
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.fhir import CodeableConcept, Reference, Meta, Quantity


class ObservationCreate(BaseModel):
    """Create Observation request"""
    patient_id: int = Field(..., description="Patient reference (internal ID)")
    encounter_id: Optional[int] = Field(None, description="Encounter reference (internal ID)")
    status: str = Field(default="final", description="registered | preliminary | final | amended | corrected | cancelled")
    category: Optional[str] = Field(None, description="vital-signs | laboratory | imaging | survey")
    code: str = Field(..., description="LOINC code for what was measured")
    display: str = Field(..., description="Human-readable name")
    value_quantity: Optional[float] = Field(None, description="Numerical value")
    value_unit: Optional[str] = Field(None, description="Unit (mmHg, kg, celsius)")
    value_string: Optional[str] = Field(None, description="String value (Positive, Negative)")
    reference_range_low: Optional[float] = Field(None, description="Lower bound of normal range")
    reference_range_high: Optional[float] = Field(None, description="Upper bound of normal range")
    effective_datetime: Optional[datetime] = Field(None, description="When observation was made")
    interpretation: Optional[str] = Field(None, description="normal | high | low | critical")
    notes: Optional[str] = Field(None, description="Comments about the observation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": 1,
                "encounter_id": 1,
                "status": "final",
                "category": "vital-signs",
                "code": "85354-9",
                "display": "Blood Pressure",
                "value_quantity": 120.0,
                "value_unit": "mmHg",
                "reference_range_low": 90.0,
                "reference_range_high": 120.0,
                "effective_datetime": "2026-03-09T10:15:00Z",
                "interpretation": "normal"
            }
        }


class ObservationUpdate(BaseModel):
    """Update Observation request"""
    status: Optional[str] = None
    value_quantity: Optional[float] = None
    value_unit: Optional[str] = None
    value_string: Optional[str] = None
    interpretation: Optional[str] = None
    notes: Optional[str] = None


class ObservationResponse(BaseModel):
    """Internal Observation response (Non-FHIR)"""
    id: int
    patient_id: int
    encounter_id: Optional[int]
    status: str
    category: Optional[str]
    code: str
    display: str
    value_quantity: Optional[float]
    value_unit: Optional[str]
    value_string: Optional[str]
    reference_range_low: Optional[float]
    reference_range_high: Optional[float]
    effective_datetime: Optional[datetime]
    issued: Optional[datetime]
    interpretation: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FHIRObservation(BaseModel):
    """
    FHIR R4 Observation resource
    Full FHIR-compliant response format
    """
    resourceType: str = Field(default="Observation", const=True)
    id: str = Field(..., description="Logical id of this artifact")
    meta: Optional[Meta] = Field(None, description="Metadata about the resource")
    
    status: str = Field(..., description="registered | preliminary | final | amended | corrected | cancelled")
    category: Optional[List[CodeableConcept]] = Field(None, description="Classification of type of observation")
    
    code: CodeableConcept = Field(..., description="Type of observation (code/type)")
    subject: Reference = Field(..., description="Who/what this is about (Patient)")
    encounter: Optional[Reference] = Field(None, description="Healthcare event during which observation was made")
    
    effectiveDateTime: Optional[datetime] = Field(None, description="Clinically relevant time/time-period for observation")
    issued: Optional[datetime] = Field(None, description="Date/Time this version was made available")
    
    valueQuantity: Optional[Quantity] = Field(None, description="Actual result")
    valueString: Optional[str] = Field(None, description="Actual result (string)")
    
    interpretation: Optional[List[CodeableConcept]] = Field(None, description="High, low, normal, etc")
    note: Optional[List[dict]] = Field(None, description="Comments about the observation")
    
    referenceRange: Optional[List[dict]] = Field(None, description="Reference range for observations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Observation",
                "id": "1",
                "meta": {
                    "versionId": "1",
                    "lastUpdated": "2026-03-09T10:30:00Z"
                },
                "status": "final",
                "category": [
                    {
                        "code": "vital-signs",
                        "display": "Vital Signs",
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category"
                    }
                ],
                "code": {
                    "code": "85354-9",
                    "display": "Blood Pressure",
                    "system": "http://loinc.org"
                },
                "subject": {
                    "reference": "Patient/1",
                    "display": "John Doe"
                },
                "effectiveDateTime": "2026-03-09T10:15:00Z",
                "valueQuantity": {
                    "value": 120.0,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                },
                "interpretation": [
                    {
                        "code": "N",
                        "display": "Normal",
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
                    }
                ],
                "referenceRange": [
                    {
                        "low": {
                            "value": 90.0,
                            "unit": "mmHg"
                        },
                        "high": {
                            "value": 120.0,
                            "unit": "mmHg"
                        }
                    }
                ]
            }
        }
