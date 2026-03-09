# Phase 1 Complete - Setup & Verification Guide

## 📦 What Was Built

✅ **32 Files Created** in Phase 1:

### Backend Core (15 files)

- FastAPI application with async/await patterns
- Pydantic Settings with environment validation
- SQLAlchemy async engine (Neon PostgreSQL optimized)
- JWT authentication + bcrypt password hashing
- Health check endpoints (K8s-compatible)
- User model with RBAC (4 roles)
- Patient model (FHIR R4-aligned)
- Custom exception classes
- Pydantic validation schemas

### Testing (4 files)

- Pytest configuration with async support
- Test fixtures (database, HTTP client)
- 18 tests covering auth & health checks
- In-memory SQLite test database

### Docker & Deployment (3 files)

- Multi-stage Dockerfile (production-ready)
- Docker Compose (PostgreSQL + Redis + Backend)
- Non-root container user (security)

### Database Migrations (3 files)

- Alembic configuration
- Async migration support
- Migration template

### Documentation (5 files)

- README.md (project overview)
- Phase 1 implementation docs
- Architecture overview
- API reference with examples
- Code quality audit report

### Configuration (3 files)

- .env.example (comprehensive template)
- .gitignore (Python/Docker/IDE)
- start-dev.sh (quick start script)

---

## 🚀 Setup Instructions

### Option 1: Quick Start with Docker (Recommended)

```bash
# 1. Navigate to project
cd /Users/shyam/Projects/apcan-voice-ai

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your credentials
# Required: DATABASE_URL, GOOGLE_API_KEY, SECRET_KEY
nano .env

# 4. Run the quick start script
./start-dev.sh
```

**Visit**: http://localhost:8000/api/docs

---

### Option 2: Manual Setup (Development)

#### Step 1: Create Virtual Environment

```bash
cd /Users/shyam/Projects/apcan-voice-ai/backend

# Create venv
python3.12 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.12+
```

#### Step 2: Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (tests, linters)
pip install -r requirements-dev.txt

# Verify installations
pip list | grep fastapi
pip list | grep sqlalchemy
```

#### Step 3: Configure Environment

```bash
# Copy template
cd ..
cp .env.example .env

# Edit with your values
nano .env
```

**Required Variables**:

1. **DATABASE_URL**:

   ```
   # For Neon (FREE tier): https://neon.tech
   postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require

   # For local PostgreSQL:
   postgresql+asyncpg://user:password@localhost:5432/apcan_dev
   ```

2. **GOOGLE_API_KEY**:

   ```
   # Get from: https://aistudio.google.com/app/apikey
   AIzaSyXXX...your_key_here
   ```

3. **SECRET_KEY**:
   ```bash
   # Generate with:
   openssl rand -hex 32
   ```

#### Step 4: Setup Database

**Option A: Use Docker Compose (Easy)**

```bash
# Start just PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait 5 seconds
sleep 5

# Check if running
docker-compose ps
```

**Option B: Use Neon PostgreSQL (FREE tier)**

1. Sign up: https://neon.tech
2. Create project
3. Copy connection string to `.env`

#### Step 5: Run Database Migrations

```bash
cd backend

# Initialize Alembic (if not done)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Verify tables created
# If using Docker PostgreSQL:
docker-compose exec postgres psql -U apcan_user -d apcan_dev -c "\dt"
```

#### Step 6: Run Development Server

```bash
# Make sure you're in backend/ directory and venv is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Output should show**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

#### Step 7: Verify Installation

**Test 1: Health Check**

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

**Test 2: API Documentation**

Visit: http://localhost:8000/api/docs

You should see interactive Swagger UI with all endpoints.

**Test 3: Create User & Login**

```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "patient"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123!"
```

---

## 🧪 Running Tests

```bash
cd backend

# Ensure venv is activated
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# View coverage report
open htmlcov/index.html
```

**Expected Output**:

```
======================== 18 passed in 2.43s =========================
```

---

## 🔍 Code Quality Checks

```bash
cd backend

# Format code (auto-fix)
black app/

# Lint code
ruff check app/

# Type checking
mypy app/

# All checks should pass with 0 errors
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: "Could not connect to database"

**Solution 1**: Check if PostgreSQL is running

```bash
docker-compose ps
# Should show postgres as "UP"
```

**Solution 2**: Verify DATABASE_URL in .env

```bash
cat .env | grep DATABASE_URL
```

**Solution 3**: Test connection

```bash
# If using Docker:
docker-compose exec postgres psql -U apcan_user -d apcan_dev -c "SELECT 1;"
```

### Issue: "SECRET_KEY not set"

**Solution**: Generate and add to .env

```bash
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### Issue: Port 8000 already in use

**Solution**: Use different port

```bash
uvicorn app.main:app --reload --port 8001
```

### Issue: Tests failing with "Database not found"

**Solution**: Tests use in-memory SQLite (no setup needed)

```bash
# Reinstall test dependencies
pip install pytest pytest-asyncio httpx
```

### Issue: Docker containers not starting

**Solution 1**: Check Docker is running

```bash
docker info
```

**Solution 2**: View logs

```bash
docker-compose logs backend
docker-compose logs postgres
```

**Solution 3**: Restart services

```bash
docker-compose down
docker-compose up -d
```

---

## 📊 Verification Checklist

After setup, verify all components:

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (no import errors)
- [ ] `.env` file configured with all required variables
- [ ] Database connection working
- [ ] Migrations applied (tables created)
- [ ] Server starts without errors
- [ ] Health check returns 200 OK
- [ ] API docs accessible at /api/docs
- [ ] Can create user via signup endpoint
- [ ] Can login and receive JWT token
- [ ] Tests pass (18/18)
- [ ] Code quality checks pass (black, ruff, mypy)

---

## 🎯 What to Do Next

### 1. Explore the API

Visit http://localhost:8000/api/docs and try:

- POST /auth/signup - Create an account
- POST /auth/login - Get JWT token
- GET /auth/me - Get your user info (with token)
- GET /health - Check system health

### 2. Read the Documentation

- `/docs/architecture.md` - Understand the system design
- `/docs/api-reference.md` - Detailed API documentation
- `/docs/phase-1-implementation.md` - What was built and why

### 3. Review the Code

Key files to understand:

- `backend/app/main.py` - Application entry point
- `backend/app/core/config.py` - Configuration management
- `backend/app/routers/auth.py` - Authentication logic
- `backend/app/models/user.py` - User data model

### 4. Prepare for Phase 2

Phase 2 will add:

- FHIR resource endpoints (Encounter, Appointment)
- FHIR-compliant JSON responses
- Search parameters
- Mock EHR data

---

## 💡 Tips

1. **Use API Docs**: http://localhost:8000/api/docs is your friend for testing
2. **Check Logs**: `docker-compose logs -f backend` shows real-time logs
3. **Hot Reload**: Code changes auto-reload the server (--reload flag)
4. **Database Browser**: Use pgAdmin at http://localhost:5050 (with docker-compose --profile dev-tools)
5. **Test Often**: Run `pytest` after making changes

---

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: `docker-compose logs backend`
2. **Verify environment**: `cat .env`
3. **Test database**: `docker-compose exec postgres psql -U apcan_user -d apcan_dev`
4. **Review docs**: Read `/docs/phase-1-implementation.md`
5. **Check GitHub issues**: (if applicable)

---

## 🎉 Success!

If all verification items pass, you have successfully set up APCAN Voice AI Phase 1!

**Next Step**: Review the Phase 1 implementation document and prepare for Phase 2 (FHIR Integration).

---

**Setup Guide Version**: 1.0  
**Last Updated**: March 9, 2026  
**Phase**: 1 Complete ✅
