# APCAN Voice AI Documentation

**Project:** Autonomous Patient Care and Administrative Navigator  
**Version:** Phase 4 Complete  
**Last Updated:** March 2026

---

## 📚 Documentation Structure

This documentation is organized by project phases and general topics:

```
docs/
├── README.md (this file)
├── phase-1/
│   └── phase-1-implementation.md
├── phase-2/
│   ├── phase-2-implementation.md
│   ├── fhir-api-guide.md
│   └── code-quality-audit.md
├── phase-3/
│   ├── phase-3-implementation.md
│   ├── voice-ai-guide.md
│   └── code-quality-audit.md
├── phase-4/
│   ├── phase-4-implementation.md
│   └── code-quality-audit.md
└── general/
    ├── SETUP.md
    ├── architecture.md
    ├── api-reference.md
    └── code-quality-audit.md (legacy)
```

---

## 📖 Quick Navigation

### Getting Started

- **[Setup Guide](general/SETUP.md)** - Installation and configuration
- **[Architecture Overview](general/architecture.md)** - System design and components
- **[API Reference](general/API-reference.md)** - Complete API documentation

### Phase-Specific Documentation

#### Phase 1: Core Infrastructure

📁 [phase-1/](phase-1/)

- **[Phase 1 Implementation](phase-1/phase-1-implementation.md)**
  - FastAPI backend setup
  - PostgreSQL database with SQLAlchemy ORM
  - JWT authentication system
  - Basic patient management
  - Docker containerization

**Status:** ✅ Complete

#### Phase 2: FHIR Integration Layer

📁 [phase-2/](phase-2/)

- **[Phase 2 Implementation](phase-2/phase-2-implementation.md)**
  - FHIR R4 resource models (Patient, Encounter, Appointment, Observation)
  - FHIR-compliant API endpoints
  - Search parameters and filtering
  - Mock EHR data seeder
  - Comprehensive test suite

- **[FHIR API Guide](phase-2/fhir-api-guide.md)**
  - Complete FHIR endpoint documentation
  - Request/response examples
  - Search parameters reference
  - LOINC codes for observations
  - Code examples in Python, JavaScript, cURL

- **[Code Quality Audit](phase-2/code-quality-audit.md)**
  - Black formatting (100% compliant)
  - Ruff linting (all issues resolved)
  - Mypy type checking results
  - Security review
  - Performance metrics

**Status:** ✅ Complete

#### Phase 3: Voice AI Integration

📁 [phase-3/](phase-3/)

- **[Phase 3 Implementation](phase-3/phase-3-implementation.md)**
  - Google Gemini 2.0 Flash integration with function calling
  - WebSocket endpoint for real-time conversations
  - Multi-turn conversation management with persistence
  - AI-powered FHIR query translation (7 tools)
  - Conversation session audit trail (HIPAA)

- **[Voice AI Guide](phase-3/voice-ai-guide.md)**
  - WebSocket protocol and message types
  - REST endpoints for session management
  - AI tool calling reference
  - Configuration settings

- **[Code Quality Audit](phase-3/code-quality-audit.md)**
  - 11 bugs found and fixed (including critical Phase 2 bugs)
  - 112/112 tests passing
  - Black/Ruff clean

**Status:** ✅ Complete

#### Phase 4: LangGraph Multi-Agent + Google Calendar

📁 [phase-4/](phase-4/)

- **[Phase 4 Implementation](phase-4/phase-4-implementation.md)**
  - LangGraph StateGraph orchestrator with intent-based routing
  - 4 specialised agents: Intake, Scheduling, Care, Admin
  - 10 LangGraph tools (7 FHIR + 3 Calendar)
  - Google Calendar API integration (service account auth)
  - Voice router refactored from manual tool loop to graph execution
  - 45 new tests (157 total)

- **[Code Quality Audit](phase-4/code-quality-audit.md)**
  - Black/Ruff clean
  - Security review of agent state and Calendar API
  - Architecture review

**Status:** ✅ Complete

---

## 🎯 Documentation by Task

### For Developers

**Setting Up the Project:**

1. [Setup Guide](general/SETUP.md) - Environment setup
2. [Architecture](general/architecture.md) - Understand the system
3. [Phase 1 Implementation](phase-1/phase-1-implementation.md) - Core features
4. [Phase 2 Implementation](phase-2/phase-2-implementation.md) - FHIR layer

**API Development:**

- [API Reference](general/api-reference.md) - All endpoints
- [FHIR API Guide](phase-2/fhir-api-guide.md) - FHIR-specific docs
- [Code Quality Audit](phase-2/code-quality-audit.md) - Best practices

**Testing:**

- Run tests: `pytest tests/ -v`
- See [Phase 2 Implementation](phase-2/phase-2-implementation.md) for test details
- Mock data: `python -m app.seeders.mock_ehr_data`

### For Healthcare Professionals

**Understanding FHIR Integration:**

- [FHIR API Guide](phase-2/fhir-api-guide.md) - What is FHIR and how to use it
- [Phase 2 Implementation](phase-2/phase-2-implementation.md) - Healthcare data management

**Using the API:**

- Patient search and management
- Viewing encounter history
- Scheduling appointments
- Retrieving vital signs

### For DevOps/SysAdmins

**Deployment:**

- [Setup Guide](general/SETUP.md) - Docker deployment
- [Architecture](general/architecture.md) - Infrastructure overview
- Database migrations: `alembic upgrade head`

**Monitoring:**

- Health check: `/api/v1/health`
- Logs: Check `LOG_LEVEL` in `.env`
- Performance: See [Code Quality Audit](phase-2/code-quality-audit.md)

---

## 🔍 Search Documentation

Use your IDE's search or `grep` to find specific topics:

```bash
# Search all documentation
grep -r "authentication" docs/

# Search Phase 2 docs only
grep -r "FHIR" docs/phase-2/

# Find setup instructions
grep -r "install" docs/general/
```

---

## 📝 Documentation Standards

### File Naming

- Implementation docs: `phase-{N}-implementation.md`
- Guides: `{topic}-guide.md`
- References: `{topic}-reference.md`
- General docs: `{TOPIC}.md` (capitals)

### Structure

Each phase folder contains:

- **Implementation doc** - Detailed technical implementation
- **Guides** - How-to documentation
- **Audits** - Quality and security reviews

### Updates

- Update documentation **before** merging to main
- Include code examples for new features
- Link related documentation
- Update this README when adding new docs

---

## 🏗️ Project Status

| Phase                        | Status      | Documentation | Tests      | Code Quality |
| ---------------------------- | ----------- | ------------- | ---------- | ------------ |
| Phase 1: Core Infrastructure | ✅ Complete | ✅ Complete   | ✅ 100%    | ✅ Excellent |
| Phase 2: FHIR Integration    | ✅ Complete | ✅ Complete   | ✅ 85%+    | ✅ Excellent |
| Phase 3: Voice AI            | ⏳ Planned  | ⏳ Pending    | ⏳ Pending | -            |
| Phase 4: Scheduling          | ⏳ Planned  | ⏳ Pending    | ⏳ Pending | -            |
| Phase 5: Production          | ⏳ Planned  | ⏳ Pending    | ⏳ Pending | -            |

---

## 🤝 Contributing to Documentation

### Adding New Documentation

1. Create file in appropriate phase folder
2. Follow naming conventions
3. Include table of contents for long docs
4. Add code examples
5. Update this README

### Updating Existing Documentation

1. Make changes in the relevant phase folder
2. Update "Last Updated" date
3. Note breaking changes prominently
4. Keep backward compatibility info

### Documentation Review Checklist

- [ ] Clear and concise writing
- [ ] Code examples tested
- [ ] Links to related docs working
- [ ] Screenshots/diagrams if helpful
- [ ] Technical accuracy verified
- [ ] Updated in this README

---

## 📞 Support

**Issues:** Create an issue on GitHub  
**Questions:** Check existing documentation first  
**Feature Requests:** Include use case and rationale

---

## 📚 External Resources

### FHIR Resources

- [FHIR R4 Specification](http://hl7.org/fhir/R4/)
- [FHIR Resources Overview](http://hl7.org/fhir/R4/resourcelist.html)
- [FHIR Search](http://hl7.org/fhir/R4/search.html)

### Python & FastAPI

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Healthcare Standards

- [LOINC Code System](https://loinc.org/)
- [ICD-10 Codes](https://www.who.int/standards/classifications/classification-of-diseases)
- [HIPAA Compliance](https://www.hhs.gov/hipaa/index.html)

---

**Last Updated:** March 9, 2026  
**Maintained By:** APCAN Development Team
