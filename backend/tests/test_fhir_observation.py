"""
Integration tests for FHIR Observation endpoints
Industry standard: pytest with async support
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_observation(client: AsyncClient, test_patient, test_encounter):
    """Test creating a new observation via FHIR API"""
    observation_data = {
        "patient_id": test_patient.id,
        "encounter_id": test_encounter.id,
        "status": "final",
        "category": "vital-signs",
        "code": "8480-6",
        "display": "Systolic blood pressure",
        "effective_datetime": datetime.now().isoformat(),
        "issued": datetime.now().isoformat(),
        "value_quantity": 120.0,
        "value_unit": "mmHg",
        "interpretation": "normal"
    }
    
    response = await client.post("/api/v1/fhir/Observation", json=observation_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["resourceType"] == "Observation"
    assert data["status"] == "final"
    assert data["code"]["coding"][0]["code"] == "8480-6"


@pytest.mark.asyncio
async def test_get_observation(client: AsyncClient, test_observation):
    """Test retrieving an observation by ID"""
    response = await client.get(f"/api/v1/fhir/Observation/{test_observation.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Observation"
    assert data["id"] == str(test_observation.id)
    assert data["status"] == test_observation.status


@pytest.mark.asyncio
async def test_get_observation_not_found(client: AsyncClient):
    """Test retrieving non-existent observation"""
    response = await client.get("/api/v1/fhir/Observation/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_observations_by_patient(client: AsyncClient, test_observation, test_patient):
    """Test searching observations by patient"""
    response = await client.get(
        "/api/v1/fhir/Observation",
        params={"patient": str(test_patient.id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_search_observations_by_encounter(client: AsyncClient, test_observation, test_encounter):
    """Test searching observations by encounter"""
    response = await client.get(
        "/api/v1/fhir/Observation",
        params={"encounter": f"Encounter/{test_encounter.id}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_search_observations_by_code(client: AsyncClient, test_observation):
    """Test searching observations by LOINC code"""
    response = await client.get(
        "/api/v1/fhir/Observation",
        params={"code": "8480-6"}  # Systolic BP
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(p["code"]["coding"][0]["code"] == "8480-6" for p in data)


@pytest.mark.asyncio
async def test_search_observations_by_category(client: AsyncClient, test_observation):
    """Test searching observations by category"""
    response = await client.get(
        "/api/v1/fhir/Observation",
        params={"category": "vital-signs"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(p["category"][0]["coding"][0]["code"] == "vital-signs" for p in data)


@pytest.mark.asyncio
async def test_update_observation(client: AsyncClient, test_observation):
    """Test updating an observation"""
    update_data = {
        "value_quantity": 125.0,
        "interpretation": "high"
    }
    
    response = await client.put(
        f"/api/v1/fhir/Observation/{test_observation.id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valueQuantity"]["value"] == 125.0


@pytest.mark.asyncio
async def test_delete_observation(client: AsyncClient, test_observation):
    """Test soft deleting an observation"""
    response = await client.delete(f"/api/v1/fhir/Observation/{test_observation.id}")
    
    assert response.status_code == 204
    
    # Verify observation is soft deleted
    get_response = await client.get(f"/api/v1/fhir/Observation/{test_observation.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_observation_with_string_value(client: AsyncClient, test_patient, test_encounter):
    """Test observation with text value instead of quantity"""
    observation_data = {
        "patient_id": test_patient.id,
        "encounter_id": test_encounter.id,
        "status": "final",
        "category": "laboratory",
        "code": "58410-2",
        "display": "Blood type",
        "effective_datetime": datetime.now().isoformat(),
        "issued": datetime.now().isoformat(),
        "value_string": "O positive"
    }
    
    response = await client.post("/api/v1/fhir/Observation", json=observation_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["valueString"] == "O positive"


@pytest.mark.asyncio
async def test_observation_fhir_compliance(client: AsyncClient, test_observation):
    """Test that observation response is FHIR R4 compliant"""
    response = await client.get(f"/api/v1/fhir/Observation/{test_observation.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required FHIR fields
    assert "resourceType" in data
    assert data["resourceType"] == "Observation"
    assert "id" in data
    assert "status" in data
    assert "code" in data
    assert "subject" in data
    
    # Check FHIR data types
    assert isinstance(data["code"], dict)
    assert "coding" in data["code"]
    assert isinstance(data["subject"], dict)
    assert "reference" in data["subject"]
    
    # Check value (either valueQuantity or valueString)
    assert "valueQuantity" in data or "valueString" in data
    
    if "valueQuantity" in data:
        assert isinstance(data["valueQuantity"], dict)
        assert "value" in data["valueQuantity"]
        assert "unit" in data["valueQuantity"]
