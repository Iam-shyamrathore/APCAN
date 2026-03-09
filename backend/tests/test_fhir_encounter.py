"""
Integration tests for FHIR Encounter endpoints
Industry standard: pytest with async support
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_encounter(client: AsyncClient, test_patient, test_provider):
    """Test creating a new encounter via FHIR API"""
    encounter_data = {
        "patient_id": test_patient.id,
        "provider_id": test_provider.id,
        "encounter_class": "outpatient",
        "status": "in-progress",
        "period_start": datetime.now().isoformat(),
        "reason_code": "R51",
        "reason_display": "Headache"
    }
    
    response = await client.post("/api/v1/fhir/Encounter", json=encounter_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["resourceType"] == "Encounter"
    assert data["status"] == "in-progress"
    assert data["class"]["code"] == "AMB"  # FHIR code for outpatient


@pytest.mark.asyncio
async def test_get_encounter(client: AsyncClient, test_encounter):
    """Test retrieving an encounter by ID"""
    response = await client.get(f"/api/v1/fhir/Encounter/{test_encounter.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Encounter"
    assert data["id"] == str(test_encounter.id)
    assert data["status"] == test_encounter.status


@pytest.mark.asyncio
async def test_get_encounter_not_found(client: AsyncClient):
    """Test retrieving non-existent encounter"""
    response = await client.get("/api/v1/fhir/Encounter/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_encounters_by_patient(client: AsyncClient, test_encounter, test_patient):
    """Test searching encounters by patient"""
    response = await client.get(
        "/api/v1/fhir/Encounter",
        params={"patient": f"Patient/{test_patient.id}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(p["subject"]["reference"] == f"Patient/{test_patient.id}" for p in data)


@pytest.mark.asyncio
async def test_search_encounters_by_status(client: AsyncClient, test_encounter):
    """Test searching encounters by status"""
    response = await client.get(
        "/api/v1/fhir/Encounter",
        params={"status": "finished"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(p["status"] == "finished" for p in data)


@pytest.mark.asyncio
async def test_update_encounter(client: AsyncClient, test_encounter):
    """Test updating an encounter"""
    update_data = {
        "status": "finished",
        "period_end": datetime.now().isoformat()
    }
    
    response = await client.put(
        f"/api/v1/fhir/Encounter/{test_encounter.id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "finished"
    assert data["period"]["end"] is not None


@pytest.mark.asyncio
async def test_delete_encounter(client: AsyncClient, test_encounter):
    """Test soft deleting an encounter"""
    response = await client.delete(f"/api/v1/fhir/Encounter/{test_encounter.id}")
    
    assert response.status_code == 204
    
    # Verify encounter is soft deleted
    get_response = await client.get(f"/api/v1/fhir/Encounter/{test_encounter.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_encounter_fhir_compliance(client: AsyncClient, test_encounter):
    """Test that encounter response is FHIR R4 compliant"""
    response = await client.get(f"/api/v1/fhir/Encounter/{test_encounter.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required FHIR fields
    assert "resourceType" in data
    assert data["resourceType"] == "Encounter"
    assert "id" in data
    assert "status" in data
    assert "class" in data
    assert "subject" in data
    
    # Check FHIR data types
    assert isinstance(data["class"], dict)
    assert "code" in data["class"]
    assert isinstance(data["subject"], dict)
    assert "reference" in data["subject"]
    
    if "period" in data:
        assert isinstance(data["period"], dict)
        assert "start" in data["period"]
