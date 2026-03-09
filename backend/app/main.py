"""
APCAN Voice AI - FastAPI Application Entry Point
Following patterns from CVision/backend/app/main.py
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth, health
from app.routers.fhir import encounter, appointment, observation, patient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown
    Industry standard: Initialize connections on startup, close on shutdown
    """
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"🚀 APCAN Voice AI started - Environment: {settings.ENVIRONMENT}")

    yield

    # Shutdown: Close connections
    await engine.dispose()
    print("👋 APCAN Voice AI shutting down gracefully")


app = FastAPI(
    title="APCAN Voice AI",
    description="Autonomous Patient Care and Administrative Navigator - Voice-First Healthcare AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS Middleware - Industry standard configuration
# Reference: CVision/backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers with API versioning
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# FHIR API routers - Phase 2
app.include_router(patient.router, prefix="/api/v1")
app.include_router(encounter.router, prefix="/api/v1")
app.include_router(appointment.router, prefix="/api/v1")
app.include_router(observation.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "APCAN Voice AI",
        "version": "1.0.0",
        "status": "operational",
        "docs": f"{settings.API_URL}/api/docs",
    }
