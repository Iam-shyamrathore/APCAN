"""
Authentication Tests
Industry standard: Test signup, login, token refresh, protected endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, test_user_data):
    """Test successful user signup"""
    response = await client.post("/api/v1/auth/signup", json=test_user_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["role"] == test_user_data["role"]
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data  # Password should never be in response


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient, test_user_data):
    """Test signup with duplicate email"""
    # Create first user
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Try to create duplicate
    response = await client.post("/api/v1/auth/signup", json=test_user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_signup_invalid_email(client: AsyncClient, test_user_data):
    """Test signup with invalid email"""
    test_user_data["email"] = "not-an-email"
    response = await client.post("/api/v1/auth/signup", json=test_user_data)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_signup_short_password(client: AsyncClient, test_user_data):
    """Test signup with password too short"""
    test_user_data["password"] = "short"
    response = await client.post("/api/v1/auth/signup", json=test_user_data)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user_data):
    """Test successful login"""
    # Create user
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],  # OAuth2 uses 'username' field
        "password": test_user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user_data):
    """Test login with wrong password"""
    # Create user
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Try login with wrong password
    login_data = {
        "username": test_user_data["email"],
        "password": "WrongPassword123!"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "SomePassword123!"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user_data):
    """Test getting current user info with valid token"""
    # Create user and login
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without token"""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user_data):
    """Test token refresh with valid refresh token"""
    # Create user and login
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh access token
    response = await client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Test token refresh with invalid refresh token"""
    response = await client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": "invalid_refresh_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(client: AsyncClient, test_user_data, db_session: AsyncSession):
    """Test that inactive users cannot login"""
    # Create user
    await client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Deactivate user
    from sqlalchemy import select, update
    from app.models.user import User
    
    stmt = update(User).where(User.email == test_user_data["email"]).values(is_active=False)
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Try to login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()
