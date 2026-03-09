"""
FHIR Observation Endpoints
Reference: http://hl7.org/fhir/R4/observation.html
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.observation import Observation
from app.models.patient import Patient
from app.schemas.fhir.observation import (
    ObservationCreate,
    ObservationUpdate,
    FHIRObservation,
)
from app.services.fhir_mapper import FHIRMapper

router = APIRouter(prefix="/fhir/Observation", tags=["FHIR Observation"])


@router.post("", response_model=FHIRObservation, status_code=status.HTTP_201_CREATED)
async def create_observation(
    observation_data: ObservationCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create new Observation resource
    FHIR operation: POST /Observation
    """
    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == observation_data.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient/{observation_data.patient_id} not found",
        )

    # Create observation
    observation = Observation(**observation_data.model_dump())
    db.add(observation)
    await db.commit()
    await db.refresh(observation)

    # Load relationships for FHIR mapping
    await db.refresh(observation, ["patient", "encounter"])

    # Return FHIR-compliant response
    return FHIRMapper.observation_to_fhir(observation)


@router.get("/{observation_id}", response_model=FHIRObservation)
async def get_observation(observation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Read Observation resource by ID
    FHIR operation: GET /Observation/{id}
    """
    result = await db.execute(
        select(Observation).where(Observation.id == observation_id, Observation.is_deleted is False)
    )
    observation = result.scalar_one_or_none()

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation/{observation_id} not found"
        )

    # Load relationships
    await db.refresh(observation, ["patient", "encounter"])

    return FHIRMapper.observation_to_fhir(observation)


@router.get("", response_model=List[FHIRObservation])
async def search_observations(
    patient: Optional[str] = Query(
        None, description="Patient reference (e.g., 'Patient/123' or '123')"
    ),
    encounter: Optional[str] = Query(
        None, description="Encounter reference (e.g., 'Encounter/456' or '456')"
    ),
    code: Optional[str] = Query(None, description="LOINC code (e.g., '8480-6' for systolic BP)"),
    category: Optional[str] = Query(
        None, description="Observation category (vital-signs, laboratory, etc.)"
    ),
    date: Optional[str] = Query(None, description="Observation date (YYYY-MM-DD)"),
    _count: int = Query(10, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search Observation resources
    FHIR operation: GET /Observation?patient=X&code=Y

    Search parameters:
    - patient: Patient reference (Patient/123 or 123)
    - encounter: Encounter reference (Encounter/456 or 456)
    - code: LOINC code for the observation
    - category: Observation category
    - date: Observation date (YYYY-MM-DD)
    - _count: Number of results (default 10, max 100)
    """
    query = select(Observation).where(Observation.is_deleted is False)

    # Filter by patient
    if patient:
        # Extract patient ID from reference (handles both "Patient/123" and "123")
        patient_id = patient.split("/")[-1]
        try:
            patient_id = int(patient_id)
            query = query.where(Observation.patient_id == patient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid patient reference: {patient}",
            )

    # Filter by encounter
    if encounter:
        encounter_id = encounter.split("/")[-1]
        try:
            encounter_id = int(encounter_id)
            query = query.where(Observation.encounter_id == encounter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid encounter reference: {encounter}",
            )

    # Filter by LOINC code
    if code:
        query = query.where(Observation.code == code)

    # Filter by category
    if category:
        query = query.where(Observation.category == category)

    # Filter by date
    if date:
        from datetime import datetime

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # Match observations on this date
            query = query.where(
                Observation.effective_datetime >= date_obj,
                Observation.effective_datetime
                < datetime(date_obj.year, date_obj.month, date_obj.day + 1),
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {date}. Use YYYY-MM-DD",
            )

    # Order by date (most recent first)
    query = query.order_by(Observation.effective_datetime.desc())

    # Limit results
    query = query.limit(_count)

    result = await db.execute(query)
    observations = result.scalars().all()

    # Load relationships for all observations
    for observation in observations:
        await db.refresh(observation, ["patient", "encounter"])

    return [FHIRMapper.observation_to_fhir(obs) for obs in observations]


@router.put("/{observation_id}", response_model=FHIRObservation)
async def update_observation(
    observation_id: int, observation_data: ObservationUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update Observation resource
    FHIR operation: PUT /Observation/{id}
    """
    result = await db.execute(
        select(Observation).where(Observation.id == observation_id, Observation.is_deleted is False)
    )
    observation = result.scalar_one_or_none()

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation/{observation_id} not found"
        )

    # Update fields
    update_data = observation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(observation, field, value)

    await db.commit()
    await db.refresh(observation, ["patient", "encounter"])

    return FHIRMapper.observation_to_fhir(observation)


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(observation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft delete Observation resource
    FHIR operation: DELETE /Observation/{id}
    Note: Uses soft delete for HIPAA compliance
    """
    result = await db.execute(
        select(Observation).where(Observation.id == observation_id, Observation.is_deleted is False)
    )
    observation = result.scalar_one_or_none()

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation/{observation_id} not found"
        )

    # Soft delete
    observation.is_deleted = True
    await db.commit()

    return None
