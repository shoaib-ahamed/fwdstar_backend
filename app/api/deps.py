"""
Authentication dependencies for FastAPI.
"""
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from fastapi import (
    Depends,
    HTTPException,
    status,
    Cookie,
    Request
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserResponse


class AuthenticationError(HTTPException):
    """Custom exception for authentication errors."""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InsufficientPermissionsError(HTTPException):
    """Custom exception for authorization errors."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class AccountLockedError(HTTPException):
    """Custom exception for locked accounts."""
    def __init__(self, locked_until: datetime):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {locked_until.strftime('%Y-%m-%d %H:%M:%S')}",
            headers={"X-Locked-Until": locked_until.isoformat()}
        )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> UserResponse:
    """
    Dependency to get the current authenticated user.

    Args:
        request: FastAPI request object
        db: Database session
        access_token: JWT access token from cookie

    Returns:
        UserResponse: Current user data

    Raises:
        AuthenticationError: If token is missing or invalid
    """
    if not access_token:
        raise AuthenticationError("Not authenticated")

    # Decode token
    payload = decode_token(access_token)
    if not payload:
        raise AuthenticationError("Invalid token")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    # Extract user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    # Check if user account is active
    if user.status != UserStatus.ACTIVE:
        raise AuthenticationError("Account is not active")

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise AccountLockedError(user.locked_until)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        status=user.status.value,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory to require specific user roles.

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Callable: Dependency function

    Raises:
        InsufficientPermissionsError: If user role is not in allowed roles
    """
    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise InsufficientPermissionsError(
                f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure user is active (alias for get_current_user for clarity).

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Active user data
    """
    return current_user


async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to require ADMIN role.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Admin user data

    Raises:
        InsufficientPermissionsError: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN.value:
        raise InsufficientPermissionsError("Admin access required")
    return current_user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> Optional[UserResponse]:
    """
    Dependency to optionally get the current user (if authenticated).

    Args:
        request: FastAPI request object
        db: Database session
        access_token: JWT access token from cookie

    Returns:
        Optional[UserResponse]: Current user data if authenticated, None otherwise
    """
    try:
        return await get_current_user(request, db, access_token)
    except HTTPException:
        return None


def get_token_from_request(request: Request, token_type: str = "access") -> Optional[str]:
    """
    Extract token from request cookies.

    Args:
        request: FastAPI request object
        token_type: Type of token ('access' or 'refresh')

    Returns:
        Optional[str]: Token value if found, None otherwise
    """
    cookie_key = f"{token_type}_token"
    return request.cookies.get(cookie_key)


# Convenience dependencies for common role combinations
require_shipper = require_role([UserRole.SHIPPER.value])
require_carrier_owner = require_role([UserRole.CARRIER_OWNER.value])
require_driver = require_role([UserRole.DRIVER.value])
require_admin = require_role([UserRole.ADMIN.value])

# Combined role dependencies
require_shipper_or_admin = require_role([UserRole.SHIPPER.value, UserRole.ADMIN.value])
require_carrier_owner_or_admin = require_role([UserRole.CARRIER_OWNER.value, UserRole.ADMIN.value])
require_driver_or_admin = require_role([UserRole.DRIVER.value, UserRole.ADMIN.value])
require_logistics_roles = require_role([
    UserRole.SHIPPER.value,
    UserRole.CARRIER_OWNER.value,
    UserRole.ADMIN.value
])
require_all_roles = require_role([
    UserRole.SHIPPER.value,
    UserRole.CARRIER_OWNER.value,
    UserRole.DRIVER.value,
    UserRole.ADMIN.value
])
