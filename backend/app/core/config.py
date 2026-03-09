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
        default=None, description="Path to Google Calendar service account JSON"
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
