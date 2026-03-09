# APCAN Voice AI - Quick Reference Card

## 🚀 Essential Commands

### Project Structure

```bash
cd /Users/shyam/Projects/apcan-voice-ai
```

### Quick Start (Docker)

```bash
# One command to start everything
./start-dev.sh

# Or manually:
cp .env.example .env        # First time only
nano .env                   # Add credentials
docker-compose up -d        # Start services
```

### Manual Setup

```bash
# Create virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate    # Mac/Linux
# OR
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup environment
cd ..
cp .env.example .env
nano .env                   # Add: DATABASE_URL, GOOGLE_API_KEY, SECRET_KEY

# Run migrations
cd backend
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Testing Commands

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_auth.py -v

# Watch mode (requires pytest-watch)
ptw

# View coverage report
open htmlcov/index.html     # Mac
xdg-open htmlcov/index.html # Linux
```

---

## 🔍 Code Quality Commands

```bash
cd backend

# Format code (auto-fix)
black app/

# Lint code
ruff check app/

# Fix linting issues
ruff check --fix app/

# Type checking
mypy app/

# Run all quality checks
black app/ && ruff check app/ && mypy app/
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Start with logs
docker-compose up

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Run tests in Docker
docker-compose exec backend pytest

# Access PostgreSQL
docker-compose exec postgres psql -U apcan_user -d apcan_dev

# Start with pgAdmin (database UI)
docker-compose --profile dev-tools up -d
# Visit: http://localhost:5050
```

---

## 🗄️ Database Commands

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description of change"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history

# Reset database (CAUTION: deletes all data)
alembic downgrade base
alembic upgrade head
```

---

## 🌐 API Testing (cURL)

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### User Signup

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "patient"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123!"

# Save the access_token from response
```

### Get Current User

```bash
# Replace YOUR_TOKEN with actual token from login
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Refresh Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh?refresh_token=YOUR_REFRESH_TOKEN"
```

---

## 🔧 Utility Commands

### Generate Secret Key

```bash
openssl rand -hex 32
```

### Check Python Version

```bash
python --version    # Should be 3.11+
```

### List Installed Packages

```bash
pip list
pip freeze > requirements-freeze.txt
```

### Check Port Usage

```bash
# Mac/Linux
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

### Kill Process on Port

```bash
# Mac/Linux
kill -9 $(lsof -ti:8000)

# Windows
# Find PID from netstat, then:
taskkill /PID <PID> /F
```

---

## 📊 Database Queries

### Connect to Database

```bash
# If using Docker
docker-compose exec postgres psql -U apcan_user -d apcan_dev

# If using Neon (replace with your URL)
psql "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require"
```

### Useful SQL Queries

```sql
-- List all tables
\dt

-- Describe table structure
\d users
\d patients

-- Count users
SELECT COUNT(*) FROM users;

-- View recent users
SELECT id, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 10;

-- Check user by email
SELECT * FROM users WHERE email = 'test@example.com';

-- Delete test user (CAUTION)
DELETE FROM users WHERE email = 'test@example.com';

-- Exit psql
\q
```

---

## 🌐 URLs to Bookmark

- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Root API**: http://localhost:8000/
- **pgAdmin** (if running): http://localhost:5050

---

## 🆘 Troubleshooting

### Check Service Status

```bash
# Docker services
docker-compose ps

# Backend logs
docker-compose logs backend | tail -50

# Check environment variables
cat .env
```

### Reset Everything

```bash
# Stop all containers
docker-compose down -v

# Remove all project containers/volumes
docker-compose down -v --remove-orphans

# Rebuild from scratch
docker-compose up -d --build
```

### Clean Python Cache

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 📖 Documentation Files

- `README.md` - Project overview
- `docs/SETUP.md` - Complete setup guide
- `docs/architecture.md` - System architecture
- `docs/api-reference.md` - API documentation
- `docs/phase-1-implementation.md` - Phase 1 details
- `docs/code-quality-audit.md` - Quality review
- `PHASE_1_COMPLETE.md` - Completion summary

---

## 💡 Pro Tips

1. **Use API Docs**: Visit `/api/docs` instead of writing cURL commands
2. **Keep Docker Running**: Faster than starting/stopping repeatedly
3. **Watch Logs**: `docker-compose logs -f backend` shows real-time errors
4. **Test in Isolation**: Use pytest's in-memory database
5. **Format Often**: Run `black app/` before committing
6. **Check Health First**: If API fails, check `/api/v1/health`

---

## ⌨️ VS Code Shortcuts

If using VS Code:

- `Cmd/Ctrl + Shift + P` → "Python: Select Interpreter" → Choose venv
- `Cmd/Ctrl + J` → Open integrated terminal
- `Cmd/Ctrl + Shift + ` ` → Split terminal
- Install extensions: Python, Pylance, Docker, REST Client

---

## 🔐 Security Reminders

- ✅ Never commit `.env` file
- ✅ Change `SECRET_KEY` in production
- ✅ Use strong passwords (8+ chars)
- ✅ Rotate tokens regularly
- ✅ Use environment variables for secrets
- ✅ Keep dependencies updated

---

**Quick Reference Version**: 1.0  
**Last Updated**: March 9, 2026  
**Phase**: 1 Complete ✅

Print this card or bookmark it for quick access during development! 🚀
