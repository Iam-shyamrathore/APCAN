# Phase 3 — Code Quality Audit Report

## Summary

| Tool  | Status       | Details                                                            |
| ----- | ------------ | ------------------------------------------------------------------ |
| Black | ✅ Pass      | 52 files formatted (line-length=100)                               |
| Ruff  | ✅ Pass      | 21 issues auto-fixed (unused imports, F-strings, etc.)             |
| Mypy  | ⚠️ 44 errors | Pre-existing Phase 2 type annotation issues in FHIR schemas/mapper |
| Tests | ✅ 112/112   | All passing (Phase 1 + Phase 2 + Phase 3)                          |

## Bugs Found & Fixed During Phase 3

### Critical Bugs (Runtime Failures)

1. **Patient model ↔ schema field mismatches** — `fhir_mapper.py`, `patient.py` router, `patient.py` schema
   - `insurance_policy_number`, `email`, `address_line1/2`, `country`, `emergency_contact_relationship` referenced but don't exist on Patient model
   - `date_of_birth` should be `birth_date`
   - **Fix**: Aligned schema, router, mapper, and tests to actual model fields

2. **SQLAlchemy `is_deleted is False` bug** — All 4 FHIR routers + conversation_manager + ai_fhir_service
   - `Model.is_deleted is False` uses Python identity check on a Column object → always evaluates to `True`
   - Every query was returning zero results (soft-deleted records invisible)
   - **Fix**: Changed 21 occurrences to `Model.is_deleted.is_(False)`

3. **Variable shadowing in `fhir_mapper.py`** — `observation_to_fhir()`
   - `code, display = interp_map.get(...)` overwrites the `CodeableConcept` variable `code`
   - Causes `FHIRObservation` validation error (receives string 'N' instead of CodeableConcept)
   - **Fix**: Renamed to `interp_code, interp_display`

4. **Missing primary keys** — `Encounter`, `Appointment`, `Observation` models
   - No `id` column defined → tables created without PK
   - **Fix**: Added `id` to `BaseModel`, removed duplicates from `Patient`/`User`/conversation models

5. **Pydantic v2 `const=True` removed** — 3 FHIR schemas
   - `Field(const=True)` deprecated in Pydantic v2 → replaced with `Literal["Type"]`

### Medium Bugs

6. **Appointment date filter overflow** — `appointment.py` router
   - `datetime(year, month, day + 1)` crashes on last day of month (e.g. Jan 31 → day 32)
   - **Fix**: Changed to `date_obj + timedelta(days=1)`

7. **AI FHIR service field name mismatches** — `ai_fhir_service.py`
   - `appointment_date` → `start_datetime`, `reason` → `comment`
   - `service_type` → `appointment_type`, `effective_date` → `effective_datetime`

8. **Patient.user_id NOT NULL constraint** — Prevented FHIR API patient creation
   - FHIR patients can exist without a linked user account
   - **Fix**: Changed `user_id` to `nullable=True`

### Test Infrastructure

9. **Test fixtures using wrong field names** — `conftest.py`
   - `date_of_birth` → `birth_date`, `note` → `comment`
   - User model has `full_name` not `given_name`/`family_name`
   - `UserRole.provider` doesn't exist → use `"clinician"`
   - `test_patient` fixture missing required `user_id` FK

10. **passlib/bcrypt 5.0 incompatibility** — Auth tests
    - bcrypt 5.0 breaks passlib's version detection
    - **Fix**: Pinned `bcrypt==4.1.3`

11. **Tests creating own AsyncClient** — `test_fhir_patient.py`
    - Tests bypassed DB dependency override → tried connecting to production DB
    - **Fix**: Refactored to use `client` fixture from conftest

## Mypy Remaining Issues (Pre-existing)

The 44 mypy errors are all in Phase 2 code (FHIR schemas/mapper) and relate to:

- Pydantic models with all-optional fields being called with partial kwargs
- `CodeableConcept` sometimes passed a `coding` list, sometimes flat fields
- `google.protobuf` missing type stubs

These are annotation-level issues, not runtime bugs. They can be addressed in a dedicated typing cleanup pass.

## Test Coverage

| Module                         | Tests   | Status          |
| ------------------------------ | ------- | --------------- |
| Auth (Phase 1)                 | 7       | ✅ All pass     |
| Health (Phase 1)               | 2       | ✅ All pass     |
| FHIR Patient (Phase 2)         | 12      | ✅ All pass     |
| FHIR Encounter (Phase 2)       | 7       | ✅ All pass     |
| FHIR Appointment (Phase 2)     | 9       | ✅ All pass     |
| FHIR Observation (Phase 2)     | 10      | ✅ All pass     |
| Conversation Manager (Phase 3) | 14      | ✅ All pass     |
| Gemini Service (Phase 3)       | 10      | ✅ All pass     |
| Voice Router (Phase 3)         | 12      | ✅ All pass     |
| AI FHIR Service (Phase 3)      | 18      | ✅ All pass     |
| Config (Phase 3)               | 6       | ✅ All pass     |
| Schemas (Phase 3)              | 5       | ✅ All pass     |
| **Total**                      | **112** | **✅ All pass** |
