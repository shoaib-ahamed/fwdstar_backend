"""
Authentication API endpoints.
"""
from typing import Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Response
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, set_auth_cookies, clear_auth_cookies
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenRefreshRequest,
    LogoutRequest,
    RegisterResponse,
    LoginResponse,
    TokenRefreshResponse,
    LogoutResponse,
    ErrorResponse,
    ValidationErrorResponse
)
from app.models.user import UserRole
import re

router = APIRouter()


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength requirements.

    Args:
        password: Password to validate

    Returns:
        True if password meets all requirements, False otherwise
    """
    # Max 8 characters
    if len(password) > 8:
        return False

    # At least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False

    # At least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False

    # At least one number
    if not re.search(r'[0-9]', password):
        return False

    return True


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
        422: {"model": ValidationErrorResponse, "description": "Invalid input"}
    }
)
async def register(
    request: Request,
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """
    Register a new user.

    Validates email uniqueness, password strength, and role validity.
    Sets httpOnly cookies with access and refresh tokens on success.
    """
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at most 8 characters with uppercase, lowercase, and number"
        )

    # Validate role
    try:
        UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"
        )

    try:
        # Create user
        user = await UserService.create_user(db, user_data)

        # Create tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id},
            remember_me=False
        )

        # Set cookies
        response_data = RegisterResponse(user=user, message="Registration successful")
        response = Response(
            content=response_data.model_dump_json(),
            status_code=status.HTTP_201_CREATED,
            media_type="application/json"
        )

        set_auth_cookies(response, access_token, refresh_token, remember_me=False)

        # Log audit event
        await AuditService.log_event(
            db=db,
            user_id=user.id,
            action="USER_REGISTERED",
            request=request,
            metadata={"email": user.email, "role": user.role}
        )

        return response_data

    except ValueError as e:
        if "Email already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account locked or inactive"},
        422: {"model": ValidationErrorResponse, "description": "Invalid input"}
    }
)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and issue tokens.

    Tracks failed login attempts and locks account after 5 failures.
    Sets httpOnly cookies with access and refresh tokens on success.
    """
    # Authenticate user
    result = await UserService.authenticate_user(db, login_data.email, login_data.password)

    if not result:
        # Log failed login attempt
        await AuditService.log_event(
            db=db,
            user_id=None,  # We don't know the user ID if auth failed
            action="USER_FAILED_LOGIN",
            request=request,
            metadata={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user, is_locked = result

    if is_locked:
        # Get updated user data to get lock expiration
        user_db = await UserService.get_user_by_email(db, login_data.email)
        if user_db and user_db.locked_until:
            await AuditService.log_event(
                db=db,
                user_id=user.id,
                action="USER_LOCKED",
                request=request,
                metadata={"email": login_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked until {user_db.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
            )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id},
        remember_me=login_data.remember_me
    )

    # Set cookies
    response_data = LoginResponse(user=user, message="Login successful")
    response = Response(
        content=response_data.model_dump_json(),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )

    set_auth_cookies(response, access_token, refresh_token, login_data.remember_me)

    # Log successful login
    await AuditService.log_event(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        request=request,
        metadata={"email": user.email, "role": user.role}
    )

    return response_data


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK
)
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> LogoutResponse:
    """
    Log out user by clearing authentication cookies.
    """
    # Clear cookies
    response = Response(
        content=LogoutResponse(message="Logged out successfully").model_dump_json(),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )

    clear_auth_cookies(response)

    # Log audit event
    await AuditService.log_event(
        db=db,
        user_id=current_user.id,
        action="USER_LOGOUT",
        request=request,
        metadata={"email": current_user.email}
    )

    return LogoutResponse(message="Logged out successfully")


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
        403: {"model": ErrorResponse, "description": "Account is inactive or locked"}
    }
)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenRefreshResponse:
    """
    Refresh access token using refresh token cookie.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # Decode refresh token
    from app.core.security import decode_token

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload"
        )

    # Verify user still exists and is active
    from app.services.user_service import UserService
    from app.models.user import User, UserStatus
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found"
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # Create new access token
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )

    # Set new access token cookie
    response_data = TokenRefreshResponse(message="Token refreshed successfully")
    response = Response(
        content=response_data.model_dump_json(),
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )

    # Get remember_me from original refresh token payload
    remember_me = payload.get("remember_me", False)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,  # Should be based on ENVIRONMENT
        samesite="lax",
        max_age=900,  # 15 minutes
        path="/"
    )

    return response_data


@router.get(
    "/me",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Account is inactive or locked"}
    }
)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current authenticated user information.
    """
    return current_user
