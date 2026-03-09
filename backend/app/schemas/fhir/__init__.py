"""
FHIR Common Elements - Shared Pydantic schemas
Industry standard: HL7 FHIR R4 datatypes
Reference: http://hl7.org/fhir/R4/datatypes.html
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CodeableConcept(BaseModel):
    """
    FHIR CodeableConcept - concept with code and display
    Example: {code: "73211009", display: "Diabetes mellitus"}
    """

    code: Optional[str] = Field(
        None, description="Code from terminology system (SNOMED, LOINC, etc.)"
    )
    display: Optional[str] = Field(None, description="Human-readable representation")
    system: Optional[str] = Field(None, description="Identity of terminology system")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "73211009",
                "display": "Diabetes mellitus",
                "system": "http://snomed.info/sct",
            }
        }


class Period(BaseModel):
    """
    FHIR Period -  time range with start and end
    """

    start: Optional[datetime] = Field(None, description="Start time with inclusive boundary")
    end: Optional[datetime] = Field(None, description="End time with inclusive boundary")

    class Config:
        json_schema_extra = {
            "example": {"start": "2026-03-09T10:00:00Z", "end": "2026-03-09T11:00:00Z"}
        }


class Identifier(BaseModel):
    """
    FHIR Identifier - unique identifier for a resource
    """

    system: Optional[str] = Field(None, description="Namespace for the identifier")
    value: str = Field(..., description="The value that is unique")
    use: Optional[str] = Field(None, description="usual | official | temp | secondary")

    class Config:
        json_schema_extra = {
            "example": {"system": "http://hospital.org/mrn", "value": "MRN12345", "use": "official"}
        }


class Reference(BaseModel):
    """
    FHIR Reference - reference to another resource
    """

    reference: str = Field(..., description="Relative, internal, or absolute URL reference")
    display: Optional[str] = Field(None, description="Text alternative for the resource")
    type: Optional[str] = Field(
        None, description="Type the reference refers to (e.g., Patient, Practitioner)"
    )

    class Config:
        json_schema_extra = {
            "example": {"reference": "Patient/123", "display": "John Doe", "type": "Patient"}
        }


class Quantity(BaseModel):
    """
    FHIR Quantity - measured amount
    """

    value: float = Field(..., description="Numerical value")
    unit: Optional[str] = Field(None, description="Unit representation (e.g., mmHg, kg)")
    system: Optional[str] = Field(None, description="System that defines coded unit form")
    code: Optional[str] = Field(None, description="Coded form of the unit")

    class Config:
        json_schema_extra = {
            "example": {
                "value": 120.0,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            }
        }


class Meta(BaseModel):
    """
    FHIR Meta - metadata about the resource
    """

    versionId: Optional[str] = Field(None, description="Version specific identifier")
    lastUpdated: Optional[datetime] = Field(
        None, description="When the resource version last changed"
    )

    class Config:
        json_schema_extra = {"example": {"versionId": "1", "lastUpdated": "2026-03-09T10:30:00Z"}}


class OperationOutcome(BaseModel):
    """
    FHIR OperationOutcome - information about operation success/failure
    Used for error responses
    """

    resourceType: str = Field(default="OperationOutcome")
    issue: List[dict] = Field(..., description="List of issues")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "not-found",
                        "diagnostics": "Resource Patient/999 not found",
                    }
                ],
            }
        }
