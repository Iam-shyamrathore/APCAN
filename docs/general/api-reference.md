# APCAN Voice AI - API Reference

**Base URL**: `http://localhost:8000` (Development)  
**API Version**: v1  
**API Prefix**: `/api/v1`

## 📚 Table of Contents

1. [Authentication](#authentication)
2. [Health Checks](#health-checks)
3. [Error Responses](#error-responses)
4. [Rate Limiting](#rate-limiting)

---

## 🔐 Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### POST /api/v1/auth/signup

Create a new user account.

**Request Body:**

```json
{
  "email": "patient@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "patient"
}
```

**Validation Rules:**

- `email`: Valid email format, not already registered
- `password`: Minimum 8 characters
- `role`: One of: `admin`, `clinician`, `patient`, `agent`

**Response:** `201 Created`

```json
{
  "id": 1,
  "email": "patient@example.com",
  "full_name": "John Doe",
  "role": "patient",
  "is_active": true,
  "created_at": "2026-03-09T10:30:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Email already registered
- `422 Unprocessable Entity`: Validation error

---

### POST /api/v1/auth/login

Login with email and password to get JWT tokens.

**Request Body (Form Data):**

```http
Content-Type: application/x-www-form-urlencoded

username=patient@example.com&password=SecurePass123!
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Details:**

- `access_token`: Valid for 30 minutes
- `refresh_token`: Valid for 7 days

**Error Responses:**

- `401 Unauthorized`: Incorrect email or password
- `403 Forbidden`: Account is inactive

---

### GET /api/v1/auth/me

Get current authenticated user information.

**Headers:**

```http
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "patient@example.com",
  "full_name": "John Doe",
  "role": "patient",
  "is_active": true,
  "created_at": "2026-03-09T10:30:00Z"
}
```

**Error Responses:**

- `401 Unauthorized`: Missing or invalid token

---

### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Query Parameters:**

- `refresh_token` (string, required): The refresh token from login

**Example Request:**

```http
POST /api/v1/auth/refresh?refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Implementation Note**: Refresh tokens are rotated on each refresh for security.

**Error Responses:**

- `401 Unauthorized`: Invalid or expired refresh token

---

## 🏥 Health Checks

### GET /api/v1/health

Comprehensive health check including database connectivity.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "environment": "development",
  "database": "connected",
  "version": "1.0.0",
  "timestamp": "2026-03-09T10:30:00Z"
}
```

**Use Cases:**

- Application health monitoring
- Pre-deployment verification
- Debugging connectivity issues

---

### GET /api/v1/readiness

Kubernetes readiness probe endpoint.

**Response:** `200 OK`

```json
{
  "ready": true
}
```

**Use Cases:**

- K8s readiness probe
- Load balancer health checks
- Deployment verification

---

### GET /api/v1/liveness

Kubernetes liveness probe endpoint.

**Response:** `200 OK`

```json
{
  "alive": true
}
```

**Use Cases:**

- K8s liveness probe
- Container restart decisions
- Deadlock detection

---

## ❌ Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code  | Meaning               | Example                                 |
| ----- | --------------------- | --------------------------------------- |
| `200` | OK                    | Successful GET, PUT, PATCH              |
| `201` | Created               | Successful POST (resource created)      |
| `400` | Bad Request           | Invalid input, business logic error     |
| `401` | Unauthorized          | Missing or invalid authentication       |
| `403` | Forbidden             | Valid auth but insufficient permissions |
| `404` | Not Found             | Resource doesn't exist                  |
| `422` | Unprocessable Entity  | Validation error                        |
| `500` | Internal Server Error | Server-side error                       |

### Example Error Responses

**401 Unauthorized:**

```json
{
  "detail": "Could not validate credentials"
}
```

**422 Validation Error:**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**400 Bad Request:**

```json
{
  "detail": "Email already registered"
}
```

---

## 🚦 Rate Limiting

**Current Status**: Not implemented (Phase 6)

**Planned Implementation**:

- 100 requests per minute per IP
- 1000 requests per hour per authenticated user
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 🔮 Coming Soon (Phase 2)

### FHIR Resources

**GET /api/v1/fhir/Patient/:id**  
Retrieve FHIR Patient resource

**POST /api/v1/fhir/Appointment**  
Create FHIR Appointment resource

**GET /api/v1/fhir/Encounter/:id**  
Retrieve FHIR Encounter resource

---

## 📝 Notes

### CORS Configuration

Development mode allows origins:

- `http://localhost:3000` (React dev server)
- `http://localhost:5173` (Vite dev server)

Production mode requires explicit origin configuration via `CORS_ORIGINS` environment variable.

### Content Types

- **Request**: `application/json` (except login: `application/x-www-form-urlencoded`)
- **Response**: `application/json`

### Timestamps

All timestamps are in ISO 8601 format with UTC timezone:

```
2026-03-09T10:30:00Z
```

### Pagination (Phase 2+)

Will follow cursor-based pagination:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

---

## 🧪 Testing with cURL

### Complete Authentication Flow

```bash
# 1. Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "patient"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123!"

# Save the access_token from response

# 3. Access Protected Route
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 4. Refresh Token
curl -X POST "http://localhost:8000/api/v1/auth/refresh?refresh_token=<refresh_token>"
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

---

## 🔧 Interactive Documentation

FastAPI provides auto-generated interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

These allow you to:

- Test endpoints directly in browser
- See request/response schemas
- Generate code samples
- View authentication requirements

---

**API Version**: 1.0.0  
**Last Updated**: March 9, 2026  
**Phase**: 1 (Core Backend Complete)
