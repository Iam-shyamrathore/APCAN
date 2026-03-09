"""Test configuration and fixtures"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session
    Industry standard: Isolated test database per test
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client
    Industry standard: Override database dependency for testing
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "patient"
    }


@pytest.fixture
def test_patient_data():
    """Sample patient data for testing"""
    return {
        "given_name": "John",
        "family_name": "Doe",
        "birth_date": "1990-01-15",
        "gender": "male",
        "phone": "+1234567890",
        "address_line": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94102"
    }


# FHIR-specific fixtures for Phase 2
@pytest_asyncio.fixture
async def test_provider(db_session: AsyncSession):
    """Create a test provider (user)"""
    from app.models.user import User
    from datetime import date
    
    provider = User(
        email="dr.test@example.com",
        hashed_password="test_hash",
        given_name="Test",
        family_name="Provider",
        role="provider"
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    return provider


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession):
    """Create a test patient for FHIR tests"""
    from app.models.patient import Patient
    from datetime import date
    
    patient = Patient(
        mrn="TEST123456",
        given_name="John",
        family_name="Doe",
        date_of_birth=date(1985, 3, 15),
        gender="male",
        phone="+1-555-123-4567",
        email="john.doe@example.com",
        address_line1="123 Main St",
        city="Springfield",
        state="IL",
        postal_code="62701",
        country="USA",
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="+1-555-987-6543",
        emergency_contact_relationship="Spouse"
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_encounter(db_session: AsyncSession, test_patient, test_provider):
    """Create a test encounter"""
    from app.models.encounter import Encounter
    from datetime import datetime, timedelta
    
    encounter = Encounter(
        patient_id=test_patient.id,
        provider_id=test_provider.id,
        encounter_class="outpatient",
        status="finished",
        period_start=datetime.now() - timedelta(days=7),
        period_end=datetime.now() - timedelta(days=7, hours=-2),
        reason_code="R51",
        reason_display="Headache"
    )
    db_session.add(encounter)
    await db_session.commit()
    await db_session.refresh(encounter)
    return encounter


@pytest_asyncio.fixture
async def test_appointment(db_session: AsyncSession, test_patient, test_provider):
    """Create a test appointment"""
    from app.models.appointment import Appointment
    from datetime import datetime, timedelta
    
    appointment = Appointment(
        patient_id=test_patient.id,
        provider_id=test_provider.id,
        status="booked",
        appointment_type="routine",
        start_datetime=datetime.now() + timedelta(days=14),
        duration_minutes=30,
        note="Routine checkup"
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


@pytest_asyncio.fixture
async def test_observation(db_session: AsyncSession, test_patient, test_encounter):
    """Create a test observation"""
    from app.models.observation import Observation
    from datetime import datetime, timedelta
    
    observation = Observation(
        patient_id=test_patient.id,
        encounter_id=test_encounter.id,
        status="final",
        category="vital-signs",
        code="8480-6",
        display="Systolic blood pressure",
        effective_datetime=datetime.now() - timedelta(days=7),
        issued=datetime.now() - timedelta(days=7, hours=-1),
        value_quantity=120.0,
        value_unit="mmHg",
        interpretation="normal"
    )
    db_session.add(observation)
    await db_session.commit()
    await db_session.refresh(observation)
    return observation

