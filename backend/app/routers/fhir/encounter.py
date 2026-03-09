"""
FHIR Encounter Endpoints
Reference: http://hl7.org/fhir/R4/encounter.html
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.schemas.fhir.encounter import (
    EncounterCreate,
    EncounterUpdate,
    FHIREncounter,
)
from app.services.fhir_mapper import FHIRMapper

router = APIRouter(prefix="/fhir/Encounter", tags=["FHIR Encounter"])


@router.post("", response_model=FHIREncounter, status_code=status.HTTP_201_CREATED)
async def create_encounter(encounter_data: EncounterCreate, db: AsyncSession = Depends(get_db)):
    """
    Create new Encounter resource
    FHIR operation: POST /Encounter
    """
    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == encounter_data.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient/{encounter_data.patient_id} not found",
        )

    # Create encounter
    encounter = Encounter(**encounter_data.model_dump())
    db.add(encounter)
    await db.commit()
    await db.refresh(encounter)

    # Load relationships for FHIR mapping
    await db.refresh(encounter, ["patient", "provider"])

    # Return FHIR-compliant response
    return FHIRMapper.encounter_to_fhir(encounter)


@router.get("/{encounter_id}", response_model=FHIREncounter)
async def get_encounter(encounter_id: int, db: AsyncSession = Depends(get_db)):
    """
    Read Encounter resource by ID
    FHIR operation: GET /Encounter/{id}
    """
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id, Encounter.is_deleted.is_(False))
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter/{encounter_id} not found"
        )

    # Load relationships
    await db.refresh(encounter, ["patient", "provider"])

    return FHIRMapper.encounter_to_fhir(encounter)


@router.get("", response_model=List[FHIREncounter])
async def search_encounters(
    patient: Optional[str] = Query(
        None, description="Patient reference (e.g., 'Patient/123' or '123')"
    ),
    status: Optional[str] = Query(None, description="Encounter status"),
    date: Optional[str] = Query(None, description="Date of encounter (YYYY-MM-DD)"),
    _count: int = Query(10, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search Encounter resources
    FHIR operation: GET /Encounter?patient=X&status=Y

    Search parameters:
    - patient: Patient reference (Patient/123 or 123)
    - status: Encounter status (planned, in-progress, finished, etc.)
    - date: Encounter date (YYYY-MM-DD)
    - _count: Number of results (default 10, max 100)
    """
    query = select(Encounter).where(Encounter.is_deleted.is_(False))

    # Filter by patient
    if patient:
        # Extract patient ID from reference (handles both "Patient/123" and "123")
        patient_id = patient.split("/")[-1]
        try:
            patient_id = int(patient_id)
            query = query.where(Encounter.patient_id == patient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid patient reference: {patient}",
            )

    # Filter by status
    if status:
        query = query.where(Encounter.status == status)

    # Filter by date
    if date:
        from datetime import datetime

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # Match encounters starting on this date
            query = query.where(
                Encounter.period_start >= date_obj,
                Encounter.period_start < datetime(date_obj.year, date_obj.month, date_obj.day + 1),
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {date}. Use YYYY-MM-DD",
            )

    # Limit results
    query = query.limit(_count)

    result = await db.execute(query)
    encounters = result.scalars().all()

    # Load relationships for all encounters
    for encounter in encounters:
        await db.refresh(encounter, ["patient", "provider"])

    return [FHIRMapper.encounter_to_fhir(enc) for enc in encounters]


@router.put("/{encounter_id}", response_model=FHIREncounter)
async def update_encounter(
    encounter_id: int, encounter_data: EncounterUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update Encounter resource
    FHIR operation: PUT /Encounter/{id}
    """
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id, Encounter.is_deleted.is_(False))
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter/{encounter_id} not found"
        )

    # Update fields
    update_data = encounter_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(encounter, field, value)

    await db.commit()
    await db.refresh(encounter, ["patient", "provider"])

    return FHIRMapper.encounter_to_fhir(encounter)


@router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_encounter(encounter_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft delete Encounter resource
    FHIR operation: DELETE /Encounter/{id}
    Note: Uses soft delete for HIPAA compliance
    """
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id, Encounter.is_deleted.is_(False))
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Encounter/{encounter_id} not found"
        )

    # Soft delete
    encounter.is_deleted = True
    await db.commit()

    return None
