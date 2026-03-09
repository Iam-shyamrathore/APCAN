# Phase 2: FHIR Integration Layer

**Status**: 🚧 IN PROGRESS  
**Started**: March 9, 2026  
**Objective**: Build FHIR R4-compliant API for healthcare data interoperability

## 📋 Overview

Phase 2 extends the APCAN backend with HL7 FHIR R4 (Fast Healthcare Interoperability Resources) support, enabling:
- Standardized patient data exchange
- EHR system integration readiness
- Voice AI agent access to structured clinical data
- Healthcare industry compliance

## 🎯 Success Criteria

- [ ] 4 FHIR resource types implemented (Patient, Encounter, Appointment, Observation)
- [ ] FHIR-compliant JSON responses matching HL7 specification
- [ ] CRUD operations for all resources
- [ ] Search parameters (by patient, date range, status)
- [ ] Mock EHR data with 50+ realistic patient records
- [ ] 30+ integration tests (100% coverage)
- [ ] Documentation aligned with FHIR R4 spec

## 🏗️ Architecture Design

### FHIR Resources to Implement

#### 1. Patient (Already done in Phase 1, will enhance)
- Core demographics
- Contact information
- Emergency contacts
- Medical Record Number (MRN)

#### 2. Encounter
- Patient visit/admission record
- Visit type (inpatient, outpatient, emergency)
- Period (start/end datetime)
- Status (planned, arrived, in-progress, finished)
- Reason for visit
- Provider reference

#### 3. Appointment
- Scheduling future patient visits
- DateTime and duration
- Status (proposed, pending, booked, fulfilled, cancelled)
- Appointment type
- Participant (patient + provider)
- Service category

#### 4. Observation
- Clinical measurements and findings
- Vital signs (BP, temperature, heart rate)
- Lab results
- Status (registered, preliminary, final, amended)
- Value with units
- Reference ranges

### Database Schema

```sql
-- Encounter table
CREATE TABLE encounters (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    provider_id INTEGER REFERENCES users(id),
    encounter_class VARCHAR(50),  -- inpatient, outpatient, emergency
    status VARCHAR(50),            -- planned, in-progress, finished, cancelled
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    reason_code VARCHAR(100),
    reason_display TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Appointment table
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    provider_id INTEGER REFERENCES users(id),
    status VARCHAR(50),            -- proposed, pending, booked, fulfilled, cancelled
    appointment_type VARCHAR(100),
    service_category VARCHAR(100),
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    duration_minutes INTEGER,
    comment TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Observation table
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    encounter_id INTEGER REFERENCES encounters(id),
    status VARCHAR(50),            -- registered, preliminary, final
    category VARCHAR(100),         -- vital-signs, laboratory, survey
    code VARCHAR(100),             -- LOINC code
    display TEXT,                  -- Human-readable name
    value_quantity NUMERIC,
    value_unit VARCHAR(50),
    reference_range_low NUMERIC,
    reference_range_high NUMERIC,
    effective_datetime TIMESTAMP,
    issued TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### API Endpoint Structure

Following FHIR RESTful API conventions:

```
GET     /api/v1/fhir/Patient              # Search patients
GET     /api/v1/fhir/Patient/{id}         # Read patient
POST    /api/v1/fhir/Patient              # Create patient
PUT     /api/v1/fhir/Patient/{id}         # Update patient
DELETE  /api/v1/fhir/Patient/{id}         # Soft delete

GET     /api/v1/fhir/Encounter            # Search encounters
GET     /api/v1/fhir/Encounter/{id}       # Read encounter
POST    /api/v1/fhir/Encounter            # Create encounter
PUT     /api/v1/fhir/Encounter/{id}       # Update encounter

GET     /api/v1/fhir/Appointment          # Search appointments
GET     /api/v1/fhir/Appointment/{id}     # Read appointment
POST    /api/v1/fhir/Appointment          # Create appointment
PUT     /api/v1/fhir/Appointment/{id}     # Update appointment

GET     /api/v1/fhir/Observation          # Search observations
GET     /api/v1/fhir/Observation/{id}     # Read observation
POST    /api/v1/fhir/Observation          # Create observation
```

### Search Parameters

Each resource supports FHIR-standard search parameters:

**Patient**:
- `?name=John` - Search by name
- `?birthdate=1990-01-15` - Search by birth date
- `?identifier=MRN12345` - Search by MRN

**Encounter**:
- `?patient=Patient/123` - Encounters for patient
- `?date=2026-03-01` - Encounters on date
- `?status=in-progress` - By status

**Appointment**:
- `?patient=Patient/123` - Appointments for patient
- `?date=2026-03-15` - Appointments on date
- `?status=booked` - By status

**Observation**:
- `?patient=Patient/123` - Observations for patient
- `?category=vital-signs` - By category
- `?code=85354-9` - By LOINC code (e.g., blood pressure)

## 📁 File Structure

```
backend/app/
├── models/
│   ├── encounter.py          # NEW: Encounter SQLAlchemy model
│   ├── appointment.py        # NEW: Appointment SQLAlchemy model
│   └── observation.py        # NEW: Observation SQLAlchemy model
│
├── schemas/
│   ├── fhir/                 # NEW: FHIR schemas folder
│   │   ├── __init__.py
│   │   ├── patient.py        # Enhanced FHIR Patient schema
│   │   ├── encounter.py      # FHIR Encounter schema
│   │   ├── appointment.py    # FHIR Appointment schema
│   │   ├── observation.py    # FHIR Observation schema
│   │   └── common.py         # FHIR common elements (CodeableConcept, etc.)
│
├── services/
│   ├── fhir_mapper.py        # NEW: SQLAlchemy ↔ FHIR transformer
│   └── search_service.py     # NEW: FHIR search parameter handler
│
├── routers/
│   └── fhir/                 # NEW: FHIR endpoints folder
│       ├── __init__.py
│       ├── patient.py        # Patient FHIR endpoints
│       ├── encounter.py      # Encounter FHIR endpoints
│       ├── appointment.py    # Appointment FHIR endpoints
│       └── observation.py    # Observation FHIR endpoints
│
└── seeders/
    └── mock_ehr_data.py      # NEW: Generate realistic test data

tests/
├── test_fhir_patient.py      # NEW: Patient FHIR tests
├── test_fhir_encounter.py    # NEW: Encounter tests
├── test_fhir_appointment.py  # NEW: Appointment tests
└── test_fhir_observation.py  # NEW: Observation tests
```

## 🔄 Implementation Steps

### Step 1: Database Models (Estimated: 30 min)
- Create Encounter model
- Create Appointment model
- Create Observation model
- Add relationships to Patient model
- Create Alembic migration

### Step 2: FHIR Schemas (Estimated: 45 min)
- Create FHIR common elements (CodeableConcept, Period, etc.)
- Create FHIR Encounter schema
- Create FHIR Appointment schema
- Create FHIR Observation schema
- Enhance Patient schema for full FHIR compliance

### Step 3: FHIR Mapper Service (Estimated: 45 min)
- SQLAlchemy → FHIR JSON transformer
- FHIR JSON → SQLAlchemy transformer
- Handle nested resources
- Format datetime to FHIR standard

### Step 4: FHIR API Endpoints (Estimated: 60 min)
- Patient FHIR endpoints (CRUD)
- Encounter FHIR endpoints (CRUD)
- Appointment FHIR endpoints (CRUD)
- Observation FHIR endpoints (CRUD)
- Search parameter handling

### Step 5: Mock EHR Data Seeder (Estimated: 30 min)
- Generate 50+ realistic patients
- Create encounters (past visits)
- Create appointments (future visits)
- Create observations (vital signs)
- CLI command to seed database

### Step 6: Integration Tests (Estimated: 60 min)
- Test Patient FHIR CRUD operations
- Test Encounter FHIR operations
- Test Appointment FHIR operations
- Test Observation FHIR operations
- Test search parameters
- Test FHIR JSON compliance

### Step 7: Documentation (Estimated: 30 min)
- Update API reference with FHIR endpoints
- Create FHIR implementation guide
- Document search parameters
- Add example requests/responses

**Total Estimated Time**: 4-5 hours

## 🧪 Testing Strategy

### Unit Tests
- FHIR mapper functions (SQLAlchemy ↔ FHIR JSON)
- Search parameter parsing
- Date range filtering

### Integration Tests
- Create FHIR resource via POST
- Read FHIR resource via GET
- Update FHIR resource via PUT
- Search with various parameters
- Verify FHIR JSON structure compliance

### Test Coverage Goals
- 100% of FHIR mapper functions
- 100% of FHIR API endpoints
- All search parameters tested
- Edge cases (missing fields, invalid dates)

## 📊 FHIR Compliance Checklist

- [ ] JSON structure matches FHIR R4 specification
- [ ] resourceType field present on all resources
- [ ] id field uses FHIR identifier format
- [ ] meta.versionId and meta.lastUpdated included
- [ ] CodeableConcept structure for coded fields
- [ ] Period structure for date ranges
- [ ] Reference structure for linked resources
- [ ] Search parameters follow FHIR conventions
- [ ] HTTP status codes match FHIR RESTful spec
- [ ] OperationOutcome for errors

## 🔍 Code Quality Standards

### From Skills
Will apply patterns from:
- `backend-dev-guidelines.md` - API design, error handling
- `clean-code.md` - Naming, function size, comments
- `code-review-checklist.md` - Security, performance, testing

### Specific Checks
- Type hints on all functions
- Docstrings with FHIR resource references
- Pydantic validation for all inputs
- Proper error handling (404, 400, 422)
- SQL injection prevention (ORM)
- No N+1 queries (use relationships)

## 🚀 Post-Implementation Tasks

- [ ] Run Alembic migration
- [ ] Seed database with mock data
- [ ] Test all endpoints via Swagger UI
- [ ] Run full test suite (pytest)
- [ ] Code quality checks (black, ruff, mypy)
- [ ] Update .env.example
- [ ] Performance testing (query optimization)

## 📝 Notes

### FHIR Resources Not Implemented (Future)
- Practitioner (provider details)
- MedicationRequest (prescriptions)
- Condition (diagnoses)
- Procedure (surgeries, treatments)
- AllergyIntolerance (detailed allergy info)

These can be added in later phases as needed for voice AI workflows.

### Design Decisions

**Why FHIR R4?**
- Industry standard (used by Epic, Cerner, etc.)
- Required for EHR integration
- Voice AI agents can speak "healthcare language"
- Future-proof for regulatory compliance

**Why Soft Deletes?**
- HIPAA: Never permanently delete patient data
- Audit trail: Track who deleted what and when
- Recovery: Can restore accidentally deleted records

**Why Search Parameters?**
- Voice AI needs to find "all appointments for patient John"
- Agents query by date: "appointments this week"
- Filter by status: "show pending appointments"

---

**Phase 2 Start**: March 9, 2026  
**Expected Completion**: March 9, 2026 (4-5 hours)  
**Dependencies**: Phase 1 complete ✅  
**Next Phase**: Phase 3 (Voice Pipeline with Gemini + Pipecat)
