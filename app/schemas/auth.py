"""
Authentication-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Schema for user registration request."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(
        max_length=8,
        description="Password must be at most 8 characters with uppercase, lowercase, and number"
    )
    role: str = Field(description="User role (SHIPPER, CARRIER_OWNER, DRIVER, or ADMIN)")


class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")
    remember_me: Optional[bool] = Field(
        default=False,
        description="If True, refresh token lasts 30 days instead of 7"
    )


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request (currently empty, uses cookie)."""
    pass


class LogoutRequest(BaseModel):
    """Schema for logout request (currently empty)."""
    pass


class UserLoginResponse(BaseModel):
    """Schema for successful login response."""
    id: str
    email: EmailStr
    role: str
    status: str


class RegisterResponse(BaseModel):
    """Schema for successful registration response."""
    user: UserResponse
    message: str = "Registration successful"


class LoginResponse(BaseModel):
    """Schema for successful login response."""
    user: UserResponse
    message: str = "Login successful"


class TokenRefreshResponse(BaseModel):
    """Schema for successful token refresh response."""
    message: str = "Token refreshed successfully"


class LogoutResponse(BaseModel):
    """Schema for successful logout response."""
    message: str = "Logged out successfully"


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    detail: list


class LockedAccountResponse(BaseModel):
    """Schema for locked account response."""
    detail: str
    locked_until: datetime
