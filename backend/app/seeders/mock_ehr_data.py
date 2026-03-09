"""
Mock EHR Data Seeder
Generates realistic patient, encounter, appointment, and observation test data
Industry standard: Follows FHIR R4 conventions and realistic medical data patterns
"""
import asyncio
import random
from datetime import datetime, timedelta, date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.patient import Patient
from app.models.user import User
from app.models.encounter import Encounter
from app.models.appointment import Appointment
from app.models.observation import Observation


# Realistic test data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Nancy", "Matthew", "Lisa",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
    "Emily", "Joshua", "Amanda", "Andrew", "Donna", "Kenneth", "Michelle", "Kevin"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King"
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Indianapolis", "Charlotte", "San Francisco", "Seattle"
]

STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "IN", "NC", "WA"]

# Medical conditions (ICD-10 codes)
MEDICAL_CONDITIONS = [
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("I10", "Essential (primary) hypertension"),
    ("J45.909", "Unspecified asthma, uncomplicated"),
    ("E78.5", "Hyperlipidemia"),
    ("M79.3", "Panniculitis"),
    ("R51", "Headache"),
    ("J02.9", "Acute pharyngitis"),
    ("K21.9", "Gastro-esophageal reflux disease"),
    ("M54.5", "Low back pain"),
    ("N39.0", "Urinary tract infection")
]

# LOINC codes for common observations
VITAL_SIGNS = [
    ("8480-6", "Systolic blood pressure", "mmHg", 90, 180),
    ("8462-4", "Diastolic blood pressure", "mmHg", 60, 120),
    ("8867-4", "Heart rate", "beats/min", 60, 100),
    ("8310-5", "Body temperature", "Cel", 36.1, 37.8),
    ("9279-1", "Respiratory rate", "breaths/min", 12, 20),
    ("29463-7", "Body weight", "kg", 50, 120),
    ("8302-2", "Body height", "cm", 150, 200),
    ("2708-6", "Oxygen saturation", "%", 95, 100)
]


async def create_test_patients(session: AsyncSession, count: int = 50) -> List[Patient]:
    """Create realistic test patients"""
    patients = []
    
    for i in range(count):
        # Generate random demographics
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        gender = random.choice(["male", "female", "other"])
        
        # Generate age between 1 and 90 years
        age_days = random.randint(365, 365 * 90)
        date_of_birth = date.today() - timedelta(days=age_days)
        
        # Generate address
        address_line1 = f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Rd', 'Blvd'])}"
        city = random.choice(CITIES)
        state = random.choice(STATES)
        postal_code = f"{random.randint(10000, 99999)}"
        
        # Generate contact info
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        
        # Generate emergency contact
        emergency_contact_name = f"{random.choice(FIRST_NAMES)} {last_name}"
        emergency_contact_phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        emergency_contact_relationship = random.choice(["Spouse", "Parent", "Sibling", "Child", "Friend"])
        
        # Generate insurance info
        insurance_provider = random.choice(["Blue Cross", "Aetna", "UnitedHealthcare", "Cigna", "Humana"])
        insurance_policy_number = f"INS{random.randint(100000, 999999)}"
        insurance_group_number = f"GRP{random.randint(1000, 9999)}"
        
        patient = Patient(
            mrn=f"MRN{str(i+1).zfill(6)}",
            given_name=first_name,
            family_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            email=email,
            address_line1=address_line1,
            city=city,
            state=state,
            postal_code=postal_code,
            country="USA",
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relationship=emergency_contact_relationship,
            insurance_provider=insurance_provider,
            insurance_policy_number=insurance_policy_number,
            insurance_group_number=insurance_group_number
        )
        
        session.add(patient)
        patients.append(patient)
    
    await session.commit()
    print(f"✅ Created {count} test patients")
    return patients


async def create_test_encounters(
    session: AsyncSession,
    patients: List[Patient],
    providers: List[User],
    count_per_patient: int = 3
) -> List[Encounter]:
    """Create historical encounters for patients"""
    encounters = []
    encounter_classes = ["outpatient", "inpatient", "emergency", "home"]
    statuses = ["finished", "finished", "finished", "in-progress"]  # Most are finished
    
    for patient in patients:
        # Create 1-5 encounters per patient
        num_encounters = random.randint(1, count_per_patient)
        
        for i in range(num_encounters):
            # Generate date in past 2 years
            days_ago = random.randint(1, 730)
            period_start = datetime.now() - timedelta(days=days_ago)
            
            # Duration: 30 min to 4 hours for outpatient, longer for inpatient
            encounter_class = random.choice(encounter_classes)
            if encounter_class == "inpatient":
                duration_hours = random.randint(24, 168)  # 1-7 days
            else:
                duration_hours = random.uniform(0.5, 4)
            
            period_end = period_start + timedelta(hours=duration_hours)
            
            # Random provider
            provider = random.choice(providers)
            
            # Random medical condition
            reason_code, reason_display = random.choice(MEDICAL_CONDITIONS)
            
            encounter = Encounter(
                patient_id=patient.id,
                provider_id=provider.id,
                encounter_class=encounter_class,
                status=random.choice(statuses),
                period_start=period_start,
                period_end=period_end if random.random() > 0.1 else None,  # 10% ongoing
                reason_code=reason_code,
                reason_display=reason_display
            )
            
            session.add(encounter)
            encounters.append(encounter)
    
    await session.commit()
    print(f"✅ Created {len(encounters)} test encounters")
    return encounters


async def create_test_appointments(
    session: AsyncSession,
    patients: List[Patient],
    providers: List[User],
    count_per_patient: int = 2
) -> List[Appointment]:
    """Create future appointments for patients"""
    appointments = []
    appointment_types = ["routine", "follow-up", "urgent", "procedure"]
    statuses = ["booked", "booked", "booked", "pending"]  # Most are booked
    
    for patient in patients:
        # Create 1-3 future appointments per patient
        num_appointments = random.randint(1, count_per_patient)
        
        for i in range(num_appointments):
            # Generate date in future (1 to 90 days)
            days_ahead = random.randint(1, 90)
            start_datetime = datetime.now() + timedelta(days=days_ahead)
            
            # Set time to business hours (8 AM to 5 PM)
            start_datetime = start_datetime.replace(
                hour=random.randint(8, 16),
                minute=random.choice([0, 15, 30, 45]),
                second=0,
                microsecond=0
            )
            
            # Duration: 15 min to 2 hours
            duration_minutes = random.choice([15, 30, 45, 60, 90, 120])
            
            # Random provider
            provider = random.choice(providers)
            
            # Random appointment type
            appointment_type = random.choice(appointment_types)
            
            appointment = Appointment(
                patient_id=patient.id,
                provider_id=provider.id,
                status=random.choice(statuses),
                appointment_type=appointment_type,
                start_datetime=start_datetime,
                duration_minutes=duration_minutes,
                note=f"{appointment_type.capitalize()} appointment with Dr. {provider.last_name}"
            )
            
            session.add(appointment)
            appointments.append(appointment)
    
    await session.commit()
    print(f"✅ Created {len(appointments)} test appointments")
    return appointments


async def create_test_observations(
    session: AsyncSession,
    encounters: List[Encounter]
) -> List[Observation]:
    """Create vital sign observations for encounters"""
    observations = []
    
    for encounter in encounters:
        # Create 3-8 vital signs per encounter
        num_observations = random.randint(3, 8)
        
        # Select random vital signs
        selected_vitals = random.sample(VITAL_SIGNS, num_observations)
        
        for loinc_code, display, unit, min_val, max_val in selected_vitals:
            # Generate realistic value
            value_quantity = round(random.uniform(min_val, max_val), 1)
            
            # Determine interpretation (normal, high, low)
            interpretation = "normal"
            if loinc_code in ["8480-6", "8462-4"]:  # Blood pressure
                if value_quantity > (max_val * 0.9):
                    interpretation = "high"
                elif value_quantity < (min_val * 1.1):
                    interpretation = "low"
            
            observation = Observation(
                patient_id=encounter.patient_id,
                encounter_id=encounter.id,
                status="final",
                category="vital-signs",
                code=loinc_code,
                display=display,
                effective_datetime=encounter.period_start,
                issued=encounter.period_start + timedelta(minutes=random.randint(5, 30)),
                value_quantity=value_quantity,
                value_unit=unit,
                interpretation=interpretation
            )
            
            session.add(observation)
            observations.append(observation)
    
    await session.commit()
    print(f"✅ Created {len(observations)} test observations")
    return observations


async def seed_mock_data():
    """Main seeder function"""
    print("🌱 Starting mock EHR data seeding...")
    
    async for session in get_async_session():
        try:
            # Get existing providers (users) or create a default one
            from sqlalchemy import select
            result = await session.execute(select(User))
            providers = list(result.scalars().all())
            
            if not providers:
                print("⚠️  No providers found. Creating default provider...")
                default_provider = User(
                    email="dr.provider@example.com",
                    hashed_password="dummy_hash",  # Not used for test data
                    first_name="John",
                    last_name="Provider",
                    role="provider"
                )
                session.add(default_provider)
                await session.commit()
                await session.refresh(default_provider)
                providers = [default_provider]
            
            print(f"👨‍⚕️ Using {len(providers)} provider(s)")
            
            # Create test data
            patients = await create_test_patients(session, count=50)
            encounters = await create_test_encounters(session, patients, providers, count_per_patient=3)
            appointments = await create_test_appointments(session, patients, providers, count_per_patient=2)
            observations = await create_test_observations(session, encounters)
            
            print("\n✨ Mock EHR data seeding completed!")
            print(f"📊 Summary:")
            print(f"   - {len(patients)} patients")
            print(f"   - {len(encounters)} encounters")
            print(f"   - {len(appointments)} appointments")
            print(f"   - {len(observations)} observations")
            
        except Exception as e:
            print(f"❌ Error seeding data: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_mock_data())
