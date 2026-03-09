"""
Integration tests for FHIR Appointment endpoints
Industry standard: pytest with async support
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_appointment(client: AsyncClient, test_patient, test_provider):
    """Test creating a new appointment via FHIR API"""
    future_date = datetime.now() + timedelta(days=14)
    appointment_data = {
        "patient_id": test_patient.id,
        "provider_id": test_provider.id,
        "status": "booked",
        "appointment_type": "routine",
        "start_datetime": future_date.isoformat(),
        "duration_minutes": 30,
        "note": "Annual checkup",
    }

    response = await client.post("/api/v1/fhir/Appointment", json=appointment_data)

    assert response.status_code == 201
    data = response.json()
    assert data["resourceType"] == "Appointment"
    assert data["status"] == "booked"
    assert len(data["participant"]) >= 1


@pytest.mark.asyncio
async def test_get_appointment(client: AsyncClient, test_appointment):
    """Test retrieving an appointment by ID"""
    response = await client.get(f"/api/v1/fhir/Appointment/{test_appointment.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Appointment"
    assert data["id"] == str(test_appointment.id)
    assert data["status"] == test_appointment.status


@pytest.mark.asyncio
async def test_get_appointment_not_found(client: AsyncClient):
    """Test retrieving non-existent appointment"""
    response = await client.get("/api/v1/fhir/Appointment/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_appointments_by_patient(client: AsyncClient, test_appointment, test_patient):
    """Test searching appointments by patient"""
    response = await client.get(
        "/api/v1/fhir/Appointment", params={"patient": str(test_patient.id)}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_search_appointments_by_status(client: AsyncClient, test_appointment):
    """Test searching appointments by status"""
    response = await client.get("/api/v1/fhir/Appointment", params={"status": "booked"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(p["status"] == "booked" for p in data)


@pytest.mark.asyncio
async def test_search_appointments_by_date_range(client: AsyncClient, test_appointment):
    """Test searching appointments by date range"""
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    response = await client.get(
        "/api/v1/fhir/Appointment", params={"date_ge": today, "date_le": future}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_appointment(client: AsyncClient, test_appointment):
    """Test updating an appointment"""
    update_data = {"duration_minutes": 45, "note": "Extended visit"}

    response = await client.put(f"/api/v1/fhir/Appointment/{test_appointment.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Appointment"


@pytest.mark.asyncio
async def test_cancel_appointment(client: AsyncClient, test_appointment):
    """Test cancelling an appointment"""
    response = await client.patch(
        f"/api/v1/fhir/Appointment/{test_appointment.id}/cancel",
        params={"reason": "Patient requested cancellation"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_delete_appointment(client: AsyncClient, test_appointment):
    """Test soft deleting an appointment"""
    response = await client.delete(f"/api/v1/fhir/Appointment/{test_appointment.id}")

    assert response.status_code == 204

    # Verify appointment is soft deleted
    get_response = await client.get(f"/api/v1/fhir/Appointment/{test_appointment.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_appointment_fhir_compliance(client: AsyncClient, test_appointment):
    """Test that appointment response is FHIR R4 compliant"""
    response = await client.get(f"/api/v1/fhir/Appointment/{test_appointment.id}")

    assert response.status_code == 200
    data = response.json()

    # Check required FHIR fields
    assert "resourceType" in data
    assert data["resourceType"] == "Appointment"
    assert "id" in data
    assert "status" in data
    assert "participant" in data

    # Check FHIR data types
    assert isinstance(data["participant"], list)
    assert len(data["participant"]) > 0
    assert "actor" in data["participant"][0]
    assert "status" in data["participant"][0]
