# APCAN Voice AI - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Voice Interface                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │  Patient's   │ ───▶ │   Browser    │ ───▶ │   WebSocket  │      │
│  │  Microphone  │      │   (WebRTC)   │      │   Connection │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
└───────────────────────────────────────┬─────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Voice Processing Layer                          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   Pipecat    │ ───▶ │   Gemini     │ ───▶ │  VAD + Barge │      │
│  │ Orchestrator │      │  Live API    │      │    Handler   │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
└───────────────────────────────────┬─────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Agent Layer (LangGraph)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │   Intake   │  │ Scheduling │  │    Care    │  │   Admin    │   │
│  │   Agent    │  │   Agent    │  │   Agent    │  │   Agent    │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Tool Integration Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │  Calendar  │  │    FHIR    │  │  Database  │  │    Auth    │   │
│  │   (Google) │  │   Server   │  │  (Neon)    │  │   (JWT)    │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 Directory Structure

```
apcan-voice-ai/
│
├── backend/                        # FastAPI Backend
│   ├── app/
│   │   ├── core/                   # Core infrastructure
│   │   │   ├── config.py           # Pydantic settings
│   │   │   ├── database.py         # SQLAlchemy async engine
│   │   │   ├── security.py         # JWT + bcrypt utilities
│   │   │   └── exceptions.py       # Custom exception classes
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── base.py             # BaseModel with audit fields
│   │   │   ├── user.py             # User + RBAC
│   │   │   └── patient.py          # FHIR-aligned Patient
│   │   │
│   │   ├── schemas/                # Pydantic validation schemas
│   │   │   ├── user.py             # User DTOs
│   │   │   └── patient.py          # Patient DTOs
│   │   │
│   │   ├── routers/                # API endpoints
│   │   │   ├── health.py           # Health checks
│   │   │   ├── auth.py             # Authentication
│   │   │   └── fhir.py             # (Phase 2) FHIR resources
│   │   │
│   │   ├── services/               # Business logic
│   │   │   └── (Phase 2+) Agent coordinators
│   │   │
│   │   ├── agents/                 # (Phase 4) LangGraph agents
│   │   │   ├── intake_agent.py
│   │   │   ├── scheduling_agent.py
│   │   │   └── orchestrator.py
│   │   │
│   │   ├── voice/                  # (Phase 3) Voice pipeline
│   │   │   ├── pipecat_config.py
│   │   │   ├── gemini_integration.py
│   │   │   └── websocket_handler.py
│   │   │
│   │   └── main.py                 # FastAPI application entry
│   │
│   ├── tests/                      # Test suite
│   │   ├── conftest.py             # Pytest fixtures
│   │   ├── test_health.py          # Health check tests
│   │   └── test_auth.py            # Auth tests
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── versions/               # Migration scripts
│   │   └── env.py                  # Alembic configuration
│   │
│   ├── requirements.txt            # Production dependencies
│   ├── requirements-dev.txt        # Development dependencies
│   ├── Dockerfile                  # Multi-stage Python build
│   └── pytest.ini                  # Pytest configuration
│
├── frontend/                       # (Phase 5) React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceInterface.tsx  # Voice UI component
│   │   │   └── Dashboard.tsx       # Admin dashboard
│   │   ├── hooks/
│   │   │   └── useVoiceStream.ts   # WebSocket hook
│   │   └── main.tsx
│   │
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                           # Project documentation
│   ├── phase-1-implementation.md   # This file
│   ├── architecture.md             # Architecture overview
│   └── api-reference.md            # API documentation
│
├── docker-compose.yml              # Local development orchestration
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
└── README.md                       # Project overview
```

## 🔄 Data Flow

### 1. User Authentication Flow

```
User → POST /auth/signup → Validate email → Hash password (bcrypt)
                                          ↓
                         Create User in DB → Return UserResponse
                                          ↓
User → POST /auth/login → Validate credentials → Create JWT tokens
                                               ↓
                            Return access_token + refresh_token
                                               ↓
User → GET /auth/me (with Bearer token) → Decode JWT → Return user info
```

### 2. Voice Interaction Flow (Phase 3)

```
Patient speaks → WebRTC audio → WebSocket stream
                                     ↓
              Pipecat VAD detects speech boundary
                                     ↓
              Send audio to Gemini Live API (320ms latency)
                                     ↓
              Gemini transcribes + generates response
                                     ↓
              LangGraph agent decides action:
                - Book appointment → Google Calendar tool
                - Update record → Database tool
                - Fetch info → FHIR tool
                                     ↓
              Execute tool → Return result to Gemini
                                     ↓
              Gemini speaks response → Stream to patient
```

## 🗄️ Database Schema

### User Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,  -- admin, clinician, patient, agent
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### Patient Table (FHIR-aligned)

```sql
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES users(id),
    mrn VARCHAR(50) UNIQUE,      -- Medical Record Number
    given_name VARCHAR(100),
    family_name VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(255),
    address_line VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    allergies TEXT[],
    emergency_contact JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

## 🔐 Security Architecture

### Authentication Flow

1. **Signup**: Email + password → bcrypt hash → Store in DB
2. **Login**: Validate credentials → Generate JWT (access + refresh tokens)
3. **Protected Routes**: Extract Bearer token → Decode JWT → Verify signature → Get user

### Tokens

- **Access Token**: 30 minutes, contains `user_id`, `email`, `role`
- **Refresh Token**: 7 days, used to get new access token without re-login
- **Algorithm**: HS256 (HMAC with SHA-256)

### RBAC (Role-Based Access Control)

| Role          | Permissions                                    |
| ------------- | ---------------------------------------------- |
| **Admin**     | Full system access, user management, analytics |
| **Clinician** | Patient records, schedules, prescriptions      |
| **Patient**   | Own records only, appointment booking          |
| **Agent**     | Voice AI system access, tool execution         |

## 🚀 Deployment Architecture

### Development (Docker Compose)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Backend    │────▶│  PostgreSQL  │     │    Redis     │
│  (FastAPI)   │     │   (local)    │     │   (local)    │
│  Port: 8000  │     └──────────────┘     └──────────────┘
└──────────────┘
```

### Production (Google Cloud Run)

```
┌──────────────┐
│  Cloud Run   │────▶ Neon PostgreSQL (Managed)
│  Container   │     └─ Scale-to-zero enabled
│              │
│  Auto-scale  │────▶ Redis Cloud (Managed)
│  0-100       │     └─ 30MB free tier
└──────────────┘
       │
       └─────────────▶ Google Calendar API
                       Google Gemini API
```

### Cost Optimization

| Service     | Free Tier     | Usage        | Monthly Cost |
| ----------- | ------------- | ------------ | ------------ |
| Cloud Run   | 2M requests   | Voice + API  | $0           |
| Neon DB     | 0.5GB         | Patient data | $0           |
| Gemini API  | 1,500 req/day | Voice AI     | $0           |
| Redis Cloud | 30MB          | Sessions     | $0           |
| **Total**   |               |              | **$0/month** |

## 🧪 Testing Strategy

### Unit Tests

- Test individual functions (services, utilities)
- Mock external dependencies (database, APIs)
- Fast execution (<1s)

### Integration Tests

- Test API endpoints end-to-end
- Use test database (in-memory SQLite)
- Verify request/response contracts

### E2E Tests (Phase 7)

- Test voice pipeline (audio in → response out)
- Test agent workflows (multi-turn conversations)
- Load testing (concurrent users)

### Coverage Target

- **Minimum**: 80% code coverage
- **Goal**: 90%+ for critical paths (auth, FHIR, agents)

## 📊 Monitoring & Observability (Phase 8)

### Metrics

- Request latency (p50, p95, p99)
- Error rates by endpoint
- Voice transcription accuracy
- Agent tool usage
- Database query performance

### Logging

- Structured JSON logs
- Correlation IDs for request tracing
- PII redaction for HIPAA compliance

### Alerting

- API error rate >5%
- Database connection failures
- Voice latency >1 second

## 🔮 Future Phases Overview

**Phase 2**: FHIR Integration (Encounter, Appointment, Medication resources)  
**Phase 3**: Voice Pipeline (Pipecat + Gemini Live API)  
**Phase 4**: LangGraph Agents (Intake, Scheduling, Care coordination)  
**Phase 5**: React Frontend (Voice UI, dashboard, analytics)  
**Phase 6**: Security & Compliance (PII redaction, audit logs, HIPAA)  
**Phase 7**: Testing & Metrics (E2E tests, load testing, monitoring)  
**Phase 8**: Deployment (Cloud Run, CI/CD, production config)

---

**Architecture Review**: ✅ APPROVED  
**Design Pattern**: Clean Architecture + Domain-Driven Design  
**Scalability**: Async-first, stateless, horizontally scalable  
**Maintainability**: Layered, testable, documented
