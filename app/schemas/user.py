"""
User-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    role: str


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(
        max_length=8,
        description="Password must be at most 8 characters with uppercase, lowercase, and number"
    )


class UserUpdate(BaseModel):
    """Schema for user updates (partial)."""
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response (excluding sensitive data)."""
    id: str
    status: str
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""
        from_attributes = True


class UserInDB(UserBase):
    """Schema for user in database (includes all fields)."""
    id: str
    password_hash: str
    status: str
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
