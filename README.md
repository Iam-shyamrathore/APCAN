# APCAN Voice AI 🎙️

**Autonomous Patient Care and Administrative Navigator** - A fully autonomous, voice-first AI system for healthcare administration using Google Gemini and LangGraph.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Voice-First Interface**: Sub-800ms latency voice interactions using Gemini Multimodal Live API
- **Autonomous Agents**: LangGraph-powered multi-agent system for patient intake, scheduling, and care management
- **FHIR-Compliant**: Healthcare data aligned with HL7 FHIR R4 standard
- **Tool Integration**: Autonomous Google Calendar booking, EHR updates, and database operations
- **HIPAA-Aligned Security**: JWT authentication, PII redaction, audit logging, RBAC
- **Cost-Optimized**: Runs entirely on FREE tiers ($0/month for development)

## 🏗️ Architecture

```
Voice Input → VAD → Gemini Live API → LangGraph Agents → Tools (Calendar/DB/FHIR) → Voice Response
```

**Tech Stack:**

- **Backend**: FastAPI + Pydantic + SQLAlchemy (Async)
- **Database**: Neon PostgreSQL (scale-to-zero)
- **AI**: Google Gemini 2.5 Flash + LangGraph
- **Voice**: Pipecat framework with WebSocket streaming
- **Auth**: JWT with bcrypt password hashing
- **Testing**: Pytest + pytest-asyncio + pytest-cov

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL database (recommend [Neon](https://neon.tech) for FREE tier)
- Google Gemini API key ([Get here](https://aistudio.google.com/app/apikey))
- Redis (optional, for session state)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd apcan-voice-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp ../.env.example ../.env

# Edit .env and add your credentials:
# - DATABASE_URL (Neon PostgreSQL connection string)
# - GOOGLE_API_KEY (Gemini API key)
# - SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Run Database Migrations

```bash
# Apply Phase 1 + Phase 2 migrations
alembic upgrade head

# Seed mock EHR data (optional - 50+ patients, encounters, appointments, observations)
python -m app.seeders.mock_ehr_data
```

### 4. Run Development Server

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/api/docs for interactive API documentation.

## 🧪 Running Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run with output
pytest -s
```

View coverage report: `open htmlcov/index.html`

## 🔒 Security

- **Authentication**: JWT tokens with 30-minute expiration
- **Password Hashing**: bcrypt with automatic salt generation
- **RBAC**: Role-based access control (admin, clinician, patient, agent)
- **Soft Deletes**: HIPAA compliance - patient data never hard deleted
- **CORS**: Configurable allowed origins
- **Input Validation**: Pydantic schemas for all requests

## 📊 API Endpoints

### Health Checks

- `GET /api/v1/health` - Service health status
- `GET /api/v1/readiness` - Kubernetes readiness probe
- `GET /api/v1/liveness` - Kubernetes liveness probe

### Authentication

- `POST /api/v1/auth/signup` - Create new user account
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info (protected)
- `POST /api/v1/auth/refresh` - Refresh access token

### FHIR Resources (Phase 2 ✅)

#### Patient Management

- `POST /api/v1/fhir/Patient` - Create patient
- `GET /api/v1/fhir/Patient/{id}` - Get patient by ID
- `GET /api/v1/fhir/Patient?family=Smith&given=John` - Search patients
- `PUT /api/v1/fhir/Patient/{id}` - Update patient
- `DELETE /api/v1/fhir/Patient/{id}` - Soft delete patient

#### Encounter Management

- `POST /api/v1/fhir/Encounter` - Create encounter
- `GET /api/v1/fhir/Encounter/{id}` - Get encounter
- `GET /api/v1/fhir/Encounter?patient=123&status=finished` - Search encounters
- `PUT /api/v1/fhir/Encounter/{id}` - Update encounter
- `DELETE /api/v1/fhir/Encounter/{id}` - Soft delete encounter

#### Appointment Management

- `POST /api/v1/fhir/Appointment` - Create appointment
- `GET /api/v1/fhir/Appointment/{id}` - Get appointment
- `GET /api/v1/fhir/Appointment?patient=123&date_ge=2026-03-01` - Search appointments
- `PATCH /api/v1/fhir/Appointment/{id}/cancel` - Cancel appointment
- `PUT /api/v1/fhir/Appointment/{id}` - Update appointment
- `DELETE /api/v1/fhir/Appointment/{id}` - Soft delete appointment

#### Observation Management

- `POST /api/v1/fhir/Observation` - Create observation (vital signs, lab results)
- `GET /api/v1/fhir/Observation/{id}` - Get observation
- `GET /api/v1/fhir/Observation?patient=123&code=8480-6` - Search observations
- `PUT /api/v1/fhir/Observation/{id}` - Update observation
- `DELETE /api/v1/fhir/Observation/{id}` - Soft delete observation

**📚 Full FHIR API Documentation:** [docs/phase-2/fhir-api-guide.md](docs/phase-2/fhir-api-guide.md)

### Voice AI (Phase 3 ✅)

- `WS /api/v1/voice/ws?token={jwt}` - Real-time AI conversation (WebSocket)
- `GET /api/v1/voice/sessions/{id}` - Get conversation history
- `POST /api/v1/voice/sessions/{id}/end` - End conversation session

**AI Tools Available**: search_patients, get_patient, get_patient_encounters, get_patient_appointments, book_appointment, cancel_appointment, get_patient_observations

**📚 Voice AI Guide:** [docs/phase-3/voice-ai-guide.md](docs/phase-3/voice-ai-guide.md)

### Coming Soon (Phases 4-5)

- LangGraph multi-agent workflows
- Google Calendar integration
- Voice-to-text with Pipecat framework

## 📁 Project Structure

```
apcan-voice-ai/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, database, security
│   │   ├── models/        # SQLAlchemy ORM models (Patient, Encounter, Appointment, Observation, Conversation)
│   │   ├── routers/       # API endpoints
│   │   │   ├── fhir/      # FHIR R4 compliant endpoints (Phase 2)
│   │   │   └── voice.py   # WebSocket + REST voice AI endpoints (Phase 3)
│   │   ├── schemas/       # Pydantic validation schemas
│   │   │   ├── fhir/      # FHIR resource schemas (Phase 2)
│   │   │   └── voice/     # WebSocket message types (Phase 3)
│   │   ├── services/      # Business logic
│   │   │   ├── fhir_mapper.py        # SQLAlchemy ↔ FHIR transformation
│   │   │   ├── gemini_service.py     # Gemini 2.0 Flash integration (Phase 3)
│   │   │   ├── ai_fhir_service.py    # AI → FHIR query bridge (Phase 3)
│   │   │   └── conversation_manager.py # Session management (Phase 3)
│   │   └── seeders/       # Mock data generators (Phase 2)
│   ├── tests/             # Unit and integration tests (112 tests)
│   ├── alembic/           # Database migrations
│   └── venv/              # Python virtual environment
├── docs/                  # 📚 Project documentation
│   ├── README.md          # Documentation index
│   ├── phase-1/           # Phase 1: Core Infrastructure docs
│   ├── phase-2/           # Phase 2: FHIR Integration docs
│   ├── phase-3/           # Phase 3: Voice AI Integration docs
│   │   ├── phase-3-implementation.md
│   │   ├── voice-ai-guide.md
│   │   └── code-quality-audit.md
│   └── general/           # Setup, architecture, API reference
└── .env.example           # Environment configuration template
```

## 💰 Cost Optimization

This project is designed to run on **$0/month** using free tiers:

| Service              | Free Tier     | Usage    |
| -------------------- | ------------- | -------- |
| **Gemini 2.5 Flash** | 1,500 req/day | Voice AI |
| **Neon PostgreSQL**  | 0.5GB storage | Database |
| **Google Cloud Run** | 2M req/month  | Hosting  |
| **Redis Cloud**      | 30MB memory   | Sessions |

## 🧑‍💻 Development

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff check app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 📖 Documentation

- [Phase 1 Implementation](docs/phase-1-implementation.md) - Current phase
- [Architecture Overview](docs/architecture.md) - System design
- [API Reference](docs/api-reference.md) - Endpoint documentation
  **Quick Links:**
- 📚 [Documentation Index](docs/README.md) - All documentation organized by phase
- 🏗️ [Architecture Overview](docs/general/architecture.md) - System design and components
- ⚙️ [Setup Guide](docs/general/SETUP.md) - Detailed installation instructions
- 📖 [API Reference](docs/general/api-reference.md) - All API endpoints

**Phase Documentation:**

- ✅ [Phase 1: Core Infrastructure](docs/phase-1/phase-1-implementation.md) - Complete
- ✅ [Phase 2: FHIR Integration](docs/phase-2/phase-2-implementation.md) - Complete
  - 📘 [FHIR API Guide](docs/phase-2/fhir-api-guide.md) - Complete endpoint documentation
  - 🔍 [Code Quality Audit](docs/phase-2/code-quality-audit.md) - Black, Ruff, Mypy results
- ⏳ Phase 3: Voice AI Integration - Coming so
  This is a learning project following industry best practices. See implementation phases in `/docs`.

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Architecture patterns from [CVision](https://github.com/yourusername/CVision) project
- Voice AI insights from [Pipecat framework](https://github.com/pipecat-ai/pipecat)
- Healthcare standards from [HL7 FHIR R4](https://www.hl7.org/fhir/)

---

**Status**: Phase 1 Complete ✅ | Next: Phase 2 (FHIR Integration) 🚧

Built with ❤️ as a portfolio project demonstrating enterprise-grade AI engineering
