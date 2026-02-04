"""
Security utilities for JWT tokens, password hashing, and cookie management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Response
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (user id, email, role)
        expires_delta: Custom expiration time (defaults to 15 minutes)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], remember_me: bool = False) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token (user id)
        remember_me: If True, token expires in 30 days, else 7 days

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if remember_me:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    remember_me: bool = False
) -> None:
    """
    Set secure HTTP-only cookies for tokens.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        remember_me: If True, refresh cookie lasts 30 days, else 7 days
    """
    # Determine if we're in production
    is_production = settings.ENVIRONMENT == "production"

    # Access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Cannot be accessed by JavaScript (XSS protection)
        secure=is_production,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 15 minutes in seconds
        path="/",
        domain=None  # Use default domain
    )

    # Refresh token cookie (7 or 30 days)
    refresh_max_age = (settings.REFRESH_TOKEN_EXPIRE_DAYS if remember_me else 7) * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=refresh_max_age,
        path="/api/v1/auth",  # Only sent to auth endpoints
        domain=None
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear authentication cookies by setting them with max_age=0.

    Args:
        response: FastAPI Response object
    """
    # Clear access token cookie
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=0,
        path="/"
    )

    # Clear refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=0,
        path="/api/v1/auth"
    )
