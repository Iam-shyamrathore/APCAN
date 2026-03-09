"""
Integration tests for FHIR Patient endpoints
Industry standard: pytest with async support
"""
import pytest
from httpx import AsyncClient
from datetime import date

from app.main import app
from app.models.patient import Patient


@pytest.mark.asyncio
async def test_create_patient():
    """Test creating a new patient via FHIR API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        patient_data = {
            "mrn": "TEST001",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1985-03-15",
            "gender": "male",
            "phone": "+1-555-123-4567",
            "email": "john.doe@example.com",
            "address_line1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
            "country": "USA"
        }
        
        response = await client.post("/api/v1/fhir/Patient", json=patient_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["resourceType"] == "Patient"
        assert data["gender"] == "male"
        assert data["birthDate"] == "1985-03-15"
        assert len(data["name"]) > 0
        assert data["name"][0]["family"] == "Doe"
        assert "John" in data["name"][0]["given"]


@pytest.mark.asyncio
async def test_get_patient(test_patient):
    """Test retrieving a patient by ID"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/fhir/Patient/{test_patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Patient"
        assert data["id"] == str(test_patient.id)
        assert data["name"][0]["family"] == test_patient.family_name


@pytest.mark.asyncio
async def test_get_patient_not_found():
    """Test retrieving non-existent patient"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/fhir/Patient/99999")
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_patients_by_family_name(test_patient):
    """Test searching patients by family name"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/fhir/Patient",
            params={"family": test_patient.family_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(p["name"][0]["family"] == test_patient.family_name for p in data)


@pytest.mark.asyncio
async def test_search_patients_by_given_name(test_patient):
    """Test searching patients by given name"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/fhir/Patient",
            params={"given": test_patient.given_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


@pytest.mark.asyncio
async def test_search_patients_by_identifier(test_patient):
    """Test searching patients by MRN"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/fhir/Patient",
            params={"identifier": test_patient.mrn}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["identifier"][0]["value"] == test_patient.mrn


@pytest.mark.asyncio
async def test_search_patients_by_gender(test_patient):
    """Test searching patients by gender"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/fhir/Patient",
            params={"gender": "male"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(p["gender"] == "male" for p in data)


@pytest.mark.asyncio
async def test_update_patient(test_patient):
    """Test updating a patient"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        update_data = {
            "phone": "+1-555-999-8888",
            "email": "updated@example.com"
        }
        
        response = await client.put(
            f"/api/v1/fhir/Patient/{test_patient.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Patient"
        # Check if phone is updated in telecom
        phone_contact = next((t for t in data["telecom"] if t["system"] == "phone"), None)
        assert phone_contact is not None
        assert phone_contact["value"] == "+1-555-999-8888"


@pytest.mark.asyncio
async def test_delete_patient(test_patient):
    """Test soft deleting a patient"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(f"/api/v1/fhir/Patient/{test_patient.id}")
        
        assert response.status_code == 204
        
        # Verify patient is soft deleted
        get_response = await client.get(f"/api/v1/fhir/Patient/{test_patient.id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_patient_duplicate_mrn(test_patient):
    """Test creating patient with duplicate MRN"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        patient_data = {
            "mrn": test_patient.mrn,  # Duplicate MRN
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1990-01-01",
            "gender": "female"
        }
        
        response = await client.post("/api/v1/fhir/Patient", json=patient_data)
        
        assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_search_patients_pagination():
    """Test patients search with pagination"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with count parameter
        response = await client.get(
            "/api/v1/fhir/Patient",
            params={"_count": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


@pytest.mark.asyncio
async def test_patient_fhir_compliance(test_patient):
    """Test that patient response is FHIR R4 compliant"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/fhir/Patient/{test_patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required FHIR fields
        assert "resourceType" in data
        assert data["resourceType"] == "Patient"
        assert "id" in data
        assert "name" in data
        assert isinstance(data["name"], list)
        assert "gender" in data
        assert "birthDate" in data
        
        # Check FHIR data types
        assert isinstance(data["name"][0], dict)
        assert "family" in data["name"][0]
        
        if "identifier" in data:
            assert isinstance(data["identifier"], list)
            assert "system" in data["identifier"][0]
            assert "value" in data["identifier"][0]
