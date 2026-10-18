"""
MedIntel AI — Authentication Schemas.

Defines Pydantic request and response models for user registration,
login, and profile retrieval.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: str = Field(..., pattern=_EMAIL_PATTERN, description="Unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    language_preference: Optional[str] = Field("english", description="Preferred language (english, hindi, marathi, gujarati)")


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: str = Field(..., pattern=_EMAIL_PATTERN, description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class UserResponse(BaseModel):
    """User profile information returned upon authentication."""

    id: int
    name: str
    email: str
    language_preference: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Response containing user profile and bearer access token."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"
