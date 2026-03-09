"""
FHIR Appointment Endpoints
Reference: http://hl7.org/fhir/R4/appointment.html
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.schemas.fhir.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    FHIRAppointment,
)
from app.services.fhir_mapper import FHIRMapper

router = APIRouter(prefix="/fhir/Appointment", tags=["FHIR Appointment"])


@router.post("", response_model=FHIRAppointment, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create new Appointment resource
    FHIR operation: POST /Appointment
    """
    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == appointment_data.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient/{appointment_data.patient_id} not found",
        )

    # Create appointment
    appointment = Appointment(**appointment_data.model_dump())
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    # Load relationships for FHIR mapping
    await db.refresh(appointment, ["patient", "provider"])

    # Return FHIR-compliant response
    return FHIRMapper.appointment_to_fhir(appointment)


@router.get("/{appointment_id}", response_model=FHIRAppointment)
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Read Appointment resource by ID
    FHIR operation: GET /Appointment/{id}
    """
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id, Appointment.is_deleted is False)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment/{appointment_id} not found"
        )

    # Load relationships
    await db.refresh(appointment, ["patient", "provider"])

    return FHIRMapper.appointment_to_fhir(appointment)


@router.get("", response_model=List[FHIRAppointment])
async def search_appointments(
    patient: Optional[str] = Query(
        None, description="Patient reference (e.g., 'Patient/123' or '123')"
    ),
    status: Optional[str] = Query(None, description="Appointment status"),
    date: Optional[str] = Query(None, description="Appointment date (YYYY-MM-DD)"),
    date_ge: Optional[str] = Query(None, description="Appointments on or after date (YYYY-MM-DD)"),
    date_le: Optional[str] = Query(None, description="Appointments on or before date (YYYY-MM-DD)"),
    _count: int = Query(10, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search Appointment resources
    FHIR operation: GET /Appointment?patient=X&status=Y

    Search parameters:
    - patient: Patient reference (Patient/123 or 123)
    - status: Appointment status (booked, fulfilled, cancelled, etc.)
    - date: Exact appointment date (YYYY-MM-DD)
    - date_ge: Appointments on or after date (YYYY-MM-DD)
    - date_le: Appointments on or before date (YYYY-MM-DD)
    - _count: Number of results (default 10, max 100)
    """
    query = select(Appointment).where(Appointment.is_deleted is False)

    # Filter by patient
    if patient:
        # Extract patient ID from reference (handles both "Patient/123" and "123")
        patient_id = patient.split("/")[-1]
        try:
            patient_id = int(patient_id)
            query = query.where(Appointment.patient_id == patient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid patient reference: {patient}",
            )

    # Filter by status
    if status:
        query = query.where(Appointment.status == status)

    # Filter by date
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # Match appointments starting on this date
            query = query.where(
                Appointment.start_datetime >= date_obj,
                Appointment.start_datetime
                < datetime(date_obj.year, date_obj.month, date_obj.day + 1),
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {date}. Use YYYY-MM-DD",
            )

    # Filter by date range
    if date_ge:
        try:
            date_ge_obj = datetime.strptime(date_ge, "%Y-%m-%d")
            query = query.where(Appointment.start_datetime >= date_ge_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_ge format: {date_ge}. Use YYYY-MM-DD",
            )

    if date_le:
        try:
            date_le_obj = datetime.strptime(date_le, "%Y-%m-%d")
            # Include entire day
            date_le_end = datetime(
                date_le_obj.year, date_le_obj.month, date_le_obj.day
            ) + timedelta(days=1)
            query = query.where(Appointment.start_datetime < date_le_end)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_le format: {date_le}. Use YYYY-MM-DD",
            )

    # Order by date (most recent first)
    query = query.order_by(Appointment.start_datetime.desc())

    # Limit results
    query = query.limit(_count)

    result = await db.execute(query)
    appointments = result.scalars().all()

    # Load relationships for all appointments
    for appointment in appointments:
        await db.refresh(appointment, ["patient", "provider"])

    return [FHIRMapper.appointment_to_fhir(appt) for appt in appointments]


@router.put("/{appointment_id}", response_model=FHIRAppointment)
async def update_appointment(
    appointment_id: int, appointment_data: AppointmentUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update Appointment resource
    FHIR operation: PUT /Appointment/{id}
    """
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id, Appointment.is_deleted is False)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment/{appointment_id} not found"
        )

    # Update fields
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment, ["patient", "provider"])

    return FHIRMapper.appointment_to_fhir(appointment)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft delete Appointment resource
    FHIR operation: DELETE /Appointment/{id}
    Note: Uses soft delete for HIPAA compliance
    Better practice: Update status to "cancelled" instead of deleting
    """
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id, Appointment.is_deleted is False)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment/{appointment_id} not found"
        )

    # Soft delete
    appointment.is_deleted = True
    await db.commit()

    return None


@router.patch("/{appointment_id}/cancel", response_model=FHIRAppointment)
async def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an appointment (sets status to 'cancelled')
    Custom operation: PATCH /Appointment/{id}/cancel
    """
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id, Appointment.is_deleted is False)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment/{appointment_id} not found"
        )

    # Update status
    appointment.status = "cancelled"
    if reason:
        appointment.cancellation_reason = reason

    await db.commit()
    await db.refresh(appointment, ["patient", "provider"])

    return FHIRMapper.appointment_to_fhir(appointment)
