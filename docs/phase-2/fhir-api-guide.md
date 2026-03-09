# FHIR API Implementation Guide

**Phase 2 - FHIR Integration Layer**  
**Standard:** HL7 FHIR R4  
**Base URL:** `http://localhost:8000/api/v1/fhir`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [FHIR Resources](#fhir-resources)
4. [Search Parameters](#search-parameters)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [Testing](#testing)

---

## Overview

The APCAN Voice AI FHIR API provides HL7 FHIR R4 compliant endpoints for managing patient healthcare data. This enables seamless integration with Electronic Health Record (EHR) systems and supports autonomous AI agent operations.

### Supported Resources

- **Patient** - Demographics and contact information
- **Encounter** - Patient visits and clinical encounters
- **Appointment** - Scheduled future appointments
- **Observation** - Clinical measurements and vital signs

### Key Features

- Full CRUD operations on all resources
- Advanced search with multiple parameters
- FHIR R4 compliant JSON responses
- Soft delete for HIPAA compliance
- Pagination support
- Bi-directional data transformation (Internal ↔ FHIR)

---

## Authentication

### JWT Bearer Token

All FHIR endpoints require authentication via JWT bearer tokens.

```http
Authorization: Bearer <your_jwt_token>
```

### Getting a Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "provider@example.com",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## FHIR Resources

### 1. Patient Resource

#### Create Patient

```http
POST /api/v1/fhir/Patient
Content-Type: application/json
Authorization: Bearer <token>

{
  "mrn": "MRN123456",
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
  "country": "USA",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+1-555-987-6543",
  "emergency_contact_relationship": "Spouse"
}
```

**FHIR R4 Response:**

```json
{
  "resourceType": "Patient",
  "id": "123",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2026-03-09T10:30:00Z"
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/mrn",
      "value": "MRN123456"
    }
  ],
  "active": true,
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John"],
      "text": "John Doe"
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1-555-123-4567",
      "use": "home"
    },
    {
      "system": "email",
      "value": "john.doe@example.com",
      "use": "home"
    }
  ],
  "gender": "male",
  "birthDate": "1985-03-15",
  "address": [
    {
      "use": "home",
      "type": "physical",
      "line": ["123 Main St"],
      "city": "Springfield",
      "state": "IL",
      "postalCode": "62701",
      "country": "USA"
    }
  ],
  "contact": [
    {
      "relationship": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
              "code": "C",
              "display": "Spouse"
            }
          ]
        }
      ],
      "name": {
        "text": "Jane Doe"
      },
      "telecom": [
        {
          "system": "phone",
          "value": "+1-555-987-6543"
        }
      ]
    }
  ]
}
```

#### Read Patient

```http
GET /api/v1/fhir/Patient/{id}
Authorization: Bearer <token>
```

#### Update Patient

```http
PUT /api/v1/fhir/Patient/{id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "phone": "+1-555-999-8888",
  "email": "john.updated@example.com"
}
```

#### Delete Patient (Soft Delete)

```http
DELETE /api/v1/fhir/Patient/{id}
Authorization: Bearer <token>
```

#### Search Patients

```http
GET /api/v1/fhir/Patient?family=Doe&given=John&_count=10
Authorization: Bearer <token>
```

**Search Parameters:**

- `family` - Family name (last name), partial match
- `given` - Given name (first name), partial match
- `identifier` - MRN, exact match
- `birthdate` - Date of birth (YYYY-MM-DD)
- `gender` - Gender (male, female, other, unknown)
- `email` - Email address, exact match
- `phone` - Phone number, exact match
- `_count` - Results limit (default: 10, max: 100)

---

### 2. Encounter Resource

#### Create Encounter

```http
POST /api/v1/fhir/Encounter
Content-Type: application/json
Authorization: Bearer <token>

{
  "patient_id": 123,
  "provider_id": 1,
  "encounter_class": "outpatient",
  "status": "in-progress",
  "period_start": "2026-03-09T10:00:00Z",
  "reason_code": "R51",
  "reason_display": "Headache"
}
```

**FHIR R4 Response:**

```json
{
  "resourceType": "Encounter",
  "id": "456",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2026-03-09T10:30:00Z"
  },
  "status": "in-progress",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB",
    "display": "outpatient"
  },
  "subject": {
    "reference": "Patient/123",
    "type": "Patient",
    "display": "John Doe"
  },
  "participant": [
    {
      "individual": {
        "reference": "Practitioner/1",
        "display": "Dr. Provider"
      }
    }
  ],
  "period": {
    "start": "2026-03-09T10:00:00Z"
  },
  "reasonCode": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/sid/icd-10",
          "code": "R51",
          "display": "Headache"
        }
      ]
    }
  ]
}
```

#### Search Encounters

```http
GET /api/v1/fhir/Encounter?patient=Patient/123&status=finished&_count=20
Authorization: Bearer <token>
```

**Search Parameters:**

- `patient` - Patient reference (Patient/123 or 123)
- `status` - Encounter status (planned, in-progress, finished, etc.)
- `date` - Encounter date (YYYY-MM-DD)
- `_count` - Results limit

**Encounter Classes:**

- `outpatient` → FHIR code `AMB` (Ambulatory)
- `inpatient` → FHIR code `IMP` (Inpatient)
- `emergency` → FHIR code `EMER` (Emergency)
- `home` → FHIR code `HH` (Home Health)

---

### 3. Appointment Resource

#### Create Appointment

```http
POST /api/v1/fhir/Appointment
Content-Type: application/json
Authorization: Bearer <token>

{
  "patient_id": 123,
  "provider_id": 1,
  "status": "booked",
  "appointment_type": "routine",
  "start_datetime": "2026-03-20T14:00:00Z",
  "duration_minutes": 30,
  "note": "Annual checkup"
}
```

**FHIR R4 Response:**

```json
{
  "resourceType": "Appointment",
  "id": "789",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2026-03-09T10:30:00Z"
  },
  "status": "booked",
  "serviceCategory": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/service-category",
          "code": "17",
          "display": "General Practice"
        }
      ]
    }
  ],
  "start": "2026-03-20T14:00:00Z",
  "end": "2026-03-20T14:30:00Z",
  "minutesDuration": 30,
  "participant": [
    {
      "actor": {
        "reference": "Patient/123",
        "display": "John Doe"
      },
      "status": "accepted"
    },
    {
      "actor": {
        "reference": "Practitioner/1",
        "display": "Dr. Provider"
      },
      "status": "accepted"
    }
  ],
  "comment": "Annual checkup"
}
```

#### Cancel Appointment

```http
PATCH /api/v1/fhir/Appointment/{id}/cancel?reason=Patient%20requested
Authorization: Bearer <token>
```

#### Search Appointments

```http
GET /api/v1/fhir/Appointment?patient=123&date_ge=2026-03-01&date_le=2026-03-31
Authorization: Bearer <token>
```

**Search Parameters:**

- `patient` - Patient reference
- `status` - Appointment status (booked, pending, cancelled, fulfilled)
- `date` - Exact appointment date (YYYY-MM-DD)
- `date_ge` - Appointments on or after date (YYYY-MM-DD)
- `date_le` - Appointments on or before date (YYYY-MM-DD)
- `_count` - Results limit

---

### 4. Observation Resource

#### Create Observation

```http
POST /api/v1/fhir/Observation
Content-Type: application/json
Authorization: Bearer <token>

{
  "patient_id": 123,
  "encounter_id": 456,
  "status": "final",
  "category": "vital-signs",
  "code": "8480-6",
  "display": "Systolic blood pressure",
  "effective_datetime": "2026-03-09T10:15:00Z",
  "issued": "2026-03-09T10:20:00Z",
  "value_quantity": 120.0,
  "value_unit": "mmHg",
  "interpretation": "normal"
}
```

**FHIR R4 Response:**

```json
{
  "resourceType": "Observation",
  "id": "1001",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2026-03-09T10:30:00Z"
  },
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs",
          "display": "Vital Signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8480-6",
        "display": "Systolic blood pressure"
      }
    ]
  },
  "subject": {
    "reference": "Patient/123",
    "type": "Patient"
  },
  "encounter": {
    "reference": "Encounter/456"
  },
  "effectiveDateTime": "2026-03-09T10:15:00Z",
  "issued": "2026-03-09T10:20:00Z",
  "valueQuantity": {
    "value": 120.0,
    "unit": "mmHg",
    "system": "http://unitsofmeasure.org",
    "code": "mm[Hg]"
  },
  "interpretation": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
          "code": "N",
          "display": "Normal"
        }
      ]
    }
  ]
}
```

#### Search Observations

```http
GET /api/v1/fhir/Observation?patient=123&category=vital-signs&code=8480-6
Authorization: Bearer <token>
```

**Search Parameters:**

- `patient` - Patient reference
- `encounter` - Encounter reference
- `code` - LOINC code (e.g., 8480-6 for systolic BP)
- `category` - Observation category (vital-signs, laboratory, etc.)
- `date` - Observation date (YYYY-MM-DD)
- `_count` - Results limit

**Common LOINC Codes:**

- `8480-6` - Systolic blood pressure
- `8462-4` - Diastolic blood pressure
- `8867-4` - Heart rate
- `8310-5` - Body temperature
- `9279-1` - Respiratory rate
- `29463-7` - Body weight
- `8302-2` - Body height
- `2708-6` - Oxygen saturation

---

## Search Parameters

### General Search Rules

1. **Reference Parameters:** Accept both `Resource/ID` and `ID` formats
2. **Date Parameters:** Use ISO 8601 format `YYYY-MM-DD`
3. **String Parameters:** Case-insensitive, partial match (where applicable)
4. **Pagination:** Use `_count` parameter (default: 10, max: 100)

### Search Parameter Types

- **Token:** Exact match (identifier, code, status, gender)
- **String:** Partial match (family, given)
- **Date:** Date/DateTime comparisons
- **Reference:** Resource references (patient, encounter)
- **Number:** Numeric comparisons

---

## Error Handling

### FHIR OperationOutcome

All errors return FHIR OperationOutcome resources:

```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "not-found",
      "diagnostics": "Patient/99999 not found"
    }
  ]
}
```

### HTTP Status Codes

- `200 OK` - Successful GET/PUT
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing/invalid token
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource (e.g., MRN exists)
- `500 Internal Server Error` - Server error

---

## Code Examples

### Python (httpx)

```python
import httpx
from datetime import datetime

# Authenticate
async with httpx.AsyncClient() as client:
    # Login
    response = await client.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "provider@example.com", "password": "password"}
    )
    token = response.json()["access_token"]

    # Search patients
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(
        "http://localhost:8000/api/v1/fhir/Patient",
        params={"family": "Doe", "_count": 5},
        headers=headers
    )
    patients = response.json()

    # Create appointment
    appointment_data = {
        "patient_id": patients[0]["id"],
        "provider_id": 1,
        "status": "booked",
        "appointment_type": "routine",
        "start_datetime": datetime.now().isoformat(),
        "duration_minutes": 30
    }
    response = await client.post(
        "http://localhost:8000/api/v1/fhir/Appointment",
        json=appointment_data,
        headers=headers
    )
    appointment = response.json()
```

### JavaScript (fetch)

```javascript
// Authenticate
const loginResponse = await fetch("http://localhost:8000/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "provider@example.com",
    password: "password",
  }),
});
const { access_token } = await loginResponse.json();

// Search encounters
const response = await fetch(
  "http://localhost:8000/api/v1/fhir/Encounter?patient=123&status=finished",
  {
    headers: { Authorization: `Bearer ${access_token}` },
  },
);
const encounters = await response.json();
```

### cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"provider@example.com","password":"password"}' \
  | jq -r '.access_token')

# Create observation
curl -X POST http://localhost:8000/api/v1/fhir/Observation \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 123,
    "encounter_id": 456,
    "status": "final",
    "category": "vital-signs",
    "code": "8480-6",
    "display": "Systolic blood pressure",
    "effective_datetime": "2026-03-09T10:15:00Z",
    "issued": "2026-03-09T10:20:00Z",
    "value_quantity": 120.0,
    "value_unit": "mmHg",
    "interpretation": "normal"
  }'
```

---

## Testing

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/test_fhir_*.py -v
```

### Test Coverage

```bash
pytest --cov=app/routers/fhir --cov=app/services/fhir_mapper tests/
```

### Interactive API Testing

Access Swagger UI at: `http://localhost:8000/api/docs`

### Mock Data Seeder

Generate 50+ test patients with encounters, appointments, and observations:

```bash
cd backend
source venv/bin/activate
python -m app.seeders.mock_ehr_data
```

---

## References

- [FHIR R4 Specification](http://hl7.org/fhir/R4/)
- [Patient Resource](http://hl7.org/fhir/R4/patient.html)
- [Encounter Resource](http://hl7.org/fhir/R4/encounter.html)
- [Appointment Resource](http://hl7.org/fhir/R4/appointment.html)
- [Observation Resource](http://hl7.org/fhir/R4/observation.html)
- [LOINC Code System](https://loinc.org/)
- [FHIR Search Parameters](http://hl7.org/fhir/R4/search.html)
