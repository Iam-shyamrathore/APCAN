"""
User Pydantic Schemas
Industry standard: Request/response validation with Pydantic
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation"""

    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role: UserRole = Field(default=UserRole.PATIENT)


class UserResponse(UserBase):
    """Schema for user response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
