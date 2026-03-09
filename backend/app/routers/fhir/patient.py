"""
FHIR Patient Endpoints
Reference: http://hl7.org/fhir/R4/patient.html
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.patient import Patient
from app.schemas.fhir.patient import PatientCreate, PatientUpdate, FHIRPatient
from app.services.fhir_mapper import FHIRMapper

router = APIRouter(prefix="/fhir/Patient", tags=["FHIR Patient"])


@router.post("", response_model=FHIRPatient, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_data: PatientCreate, db: AsyncSession = Depends(get_db)):
    """
    Create new Patient resource
    FHIR operation: POST /Patient
    """
    # Check if MRN already exists
    result = await db.execute(select(Patient).where(Patient.mrn == patient_data.mrn))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with MRN {patient_data.mrn} already exists",
        )

    # Map fields from internal format to DB model
    patient = Patient(
        mrn=patient_data.mrn,
        given_name=patient_data.first_name,
        family_name=patient_data.last_name,
        birth_date=patient_data.date_of_birth,
        gender=patient_data.gender,
        phone=patient_data.phone,
        address_line=patient_data.address_line,
        city=patient_data.city,
        state=patient_data.state,
        postal_code=patient_data.postal_code,
        emergency_contact_name=patient_data.emergency_contact_name,
        emergency_contact_phone=patient_data.emergency_contact_phone,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    # Return FHIR-compliant response
    return FHIRMapper.patient_to_fhir(patient)


@router.get("/{patient_id}", response_model=FHIRPatient)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """
    Read Patient resource by ID
    FHIR operation: GET /Patient/{id}
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient/{patient_id} not found"
        )

    return FHIRMapper.patient_to_fhir(patient)


@router.get("", response_model=List[FHIRPatient])
async def search_patients(
    family: Optional[str] = Query(None, description="Family name (last name)"),
    given: Optional[str] = Query(None, description="Given name (first name)"),
    identifier: Optional[str] = Query(None, description="MRN or identifier"),
    birthdate: Optional[str] = Query(None, description="Date of birth (YYYY-MM-DD)"),
    gender: Optional[str] = Query(None, description="Gender (male, female, other, unknown)"),
    phone: Optional[str] = Query(None, description="Phone number"),
    _count: int = Query(10, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search Patient resources
    FHIR operation: GET /Patient?family=Smith&given=John

    Search parameters:
    - family: Family name (last name) - partial match
    - given: Given name (first name) - partial match
    - identifier: MRN - exact match
    - birthdate: Date of birth (YYYY-MM-DD) - exact match
    - gender: Gender - exact match
    - email: Email address - exact match
    - phone: Phone number - exact match
    - _count: Number of results (default 10, max 100)
    """
    query = select(Patient).where(Patient.is_deleted.is_(False))

    # Filter by family name (partial match, case-insensitive)
    if family:
        query = query.where(Patient.family_name.ilike(f"%{family}%"))

    # Filter by given name (partial match, case-insensitive)
    if given:
        query = query.where(Patient.given_name.ilike(f"%{given}%"))

    # Filter by identifier (MRN - exact match)
    if identifier:
        query = query.where(Patient.mrn == identifier)

    # Filter by birth date
    if birthdate:
        from datetime import datetime

        try:
            date_obj = datetime.strptime(birthdate, "%Y-%m-%d").date()
            query = query.where(Patient.birth_date == date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid birthdate format: {birthdate}. Use YYYY-MM-DD",
            )

    # Filter by gender
    if gender:
        query = query.where(Patient.gender == gender)

    # Filter by phone
    if phone:
        query = query.where(Patient.phone == phone)

    # Order by last name, first name
    query = query.order_by(Patient.family_name, Patient.given_name)

    # Limit results
    query = query.limit(_count)

    result = await db.execute(query)
    patients = result.scalars().all()

    return [FHIRMapper.patient_to_fhir(p) for p in patients]


@router.put("/{patient_id}", response_model=FHIRPatient)
async def update_patient(
    patient_id: int, patient_data: PatientUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update Patient resource
    FHIR operation: PUT /Patient/{id}
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient/{patient_id} not found"
        )

    # Update fields (map from internal format to DB fields)
    update_data = patient_data.model_dump(exclude_unset=True)

    # Map field names
    field_mapping = {
        "first_name": "given_name",
        "last_name": "family_name",
    }

    for field, value in update_data.items():
        db_field = field_mapping.get(field, field)
        setattr(patient, db_field, value)

    await db.commit()
    await db.refresh(patient)

    return FHIRMapper.patient_to_fhir(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft delete Patient resource
    FHIR operation: DELETE /Patient/{id}
    Note: Uses soft delete for HIPAA compliance
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient/{patient_id} not found"
        )

    # Soft delete
    patient.is_deleted = True
    await db.commit()

    return None
