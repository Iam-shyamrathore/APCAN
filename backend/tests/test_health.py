"""
Health Check Endpoint Tests
Industry standard: Test all health check endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test main health check endpoint"""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "environment" in data
    assert "database" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test Kubernetes readiness probe"""
    response = await client.get("/api/v1/readiness")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ready"] is True


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test Kubernetes liveness probe"""
    response = await client.get("/api/v1/liveness")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["alive"] is True


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root API endpoint"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "APCAN Voice AI"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"
