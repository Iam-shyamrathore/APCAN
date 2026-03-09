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
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
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

### Coming Soon (Phases 2-8)

- Voice streaming endpoints
- Patient FHIR resources
- Agent workflow triggers
- Google Calendar integration

## 📁 Project Structure

```
apcan-voice-ai/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, database, security
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic validation schemas
│   │   └── services/      # Business logic
│   ├── tests/             # Unit and integration tests
│   └── alembic/           # Database migrations
├── docs/                  # Project documentation
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

## 🤝 Contributing

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
