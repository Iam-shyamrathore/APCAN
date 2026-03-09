"""
Application Configuration - Pydantic Settings
Industry standard: Environment-based configuration with validation
Reference: CVision/backend/app/core/config.py pattern
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings with environment variable loading
    Follows 12-factor app principles
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=True)

    # API Configuration
    API_URL: str = Field(default="http://localhost:8000")
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/apcan",
        description="PostgreSQL connection string - use Neon for scale-to-zero",
    )
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (development only)")

    # Security
    SECRET_KEY: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_MINIMUM_32_CHARACTERS_REQUIRED",
        min_length=32,
        description="JWT secret key - MUST be secure",
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Google APIs
    GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API key")
    GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: str | None = Field(
        default=None, description="Path to Google Calendar service account JSON or inline JSON"
    )
    GOOGLE_CALENDAR_ID: str = Field(
        default="primary", description="Google Calendar ID for appointment events"
    )

    # LangGraph Multi-Agent - Phase 4
    LANGGRAPH_RECURSION_LIMIT: int = Field(
        default=25, ge=1, le=100, description="Max graph recursion depth"
    )
    LANGGRAPH_MAX_TOOL_ITERATIONS: int = Field(
        default=10, ge=1, le=50, description="Max tool-call loops per agent turn"
    )

    # Gemini AI - Phase 3
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=2048)
    GEMINI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)

    # Voice / WebSocket - Phase 3
    WS_MAX_CONNECTIONS: int = Field(default=100, description="Max concurrent WebSocket connections")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, description="Ping interval in seconds")
    CONVERSATION_TIMEOUT_SECONDS: int = Field(
        default=1800, description="Session timeout (30 min default)"
    )
    CONVERSATION_MAX_HISTORY: int = Field(
        default=50, description="Max messages to keep in context window"
    )

    # Redis (Session State)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is PostgreSQL"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Global settings instance
settings = Settings()
