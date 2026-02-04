"""
User service for CRUD operations.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserInDB, UserResponse
from app.core.security import hash_password, verify_password


class UserService:
    """Service for user-related operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            UserResponse: Created user data

        Raises:
            ValueError: If email already exists or role is invalid
        """
        # Validate role
        try:
            role = UserRole(user_data.role)
        except ValueError:
            raise ValueError(f"Invalid role: {user_data.role}")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        db_user = User(
            email=user_data.email,
            password_hash=password_hash,
            role=role
        )

        db.add(db_user)
        try:
            await db.commit()
            await db.refresh(db_user)
        except IntegrityError:
            await db.rollback()
            raise ValueError("Email already exists")

        return UserResponse(
            id=str(db_user.id),
            email=db_user.email,
            role=db_user.role.value,
            status=db_user.status.value,
            last_login_at=db_user.last_login_at,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserResponse]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            UserResponse if found, None otherwise
        """
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
        """
        Get user by email (includes password hash for authentication).

        Args:
            db: Database session
            email: User email

        Returns:
            UserInDB if found, None otherwise
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserInDB(
            id=str(user.id),
            email=user.email,
            password_hash=user.password_hash,
            role=user.role.value,
            status=user.status.value,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: str,
        user_update: UserUpdate
    ) -> Optional[UserResponse]:
        """
        Update user data.

        Args:
            db: Database session
            user_id: User ID
            user_update: Update data

        Returns:
            UserResponse if found and updated, None otherwise
        """
        # Build update dictionary (exclude None values)
        update_data = {}
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.role is not None:
            try:
                update_data['role'] = UserRole(user_update.role)
            except ValueError:
                raise ValueError(f"Invalid role: {user_update.role}")
        if user_update.status is not None:
            try:
                update_data['status'] = UserStatus(user_update.status)
            except ValueError:
                raise ValueError(f"Invalid status: {user_update.status}")

        if not update_data:
            # Nothing to update
            return await UserService.get_user_by_id(db, user_id)

        update_data['updated_at'] = datetime.utcnow()

        result = await db.execute(
            update(User)
            .where(User.id == UUID(user_id))
            .values(**update_data)
            .returning(User)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        await db.commit()

        return UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            update(User)
            .where(User.id == UUID(user_id))
            .values(
                status=UserStatus.SUSPENDED,
                updated_at=datetime.utcnow()
            )
            .returning(User.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await db.rollback()
            return False

        await db.commit()
        return True

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[tuple[UserResponse, bool]]:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            Tuple of (UserResponse, is_locked) or None if authentication fails
        """
        # Get user with password hash
        user_db = await UserService.get_user_by_email(db, email)
        if not user_db:
            return None

        # Check if account is locked
        if user_db.locked_until and user_db.locked_until > datetime.utcnow():
            user_response = await UserService.get_user_by_id(db, user_db.id)
            return (user_response, True) if user_response else None

        # Verify password
        if not verify_password(password, user_db.password_hash):
            # Increment failed attempts
            failed_attempts = user_db.failed_login_attempts + 1
            lock_account = failed_attempts >= 5

            lock_until = None
            if lock_account:
                lock_until = datetime.utcnow() + timedelta(minutes=30)

            await db.execute(
                update(User)
                .where(User.id == UUID(user_db.id))
                .values(
                    failed_login_attempts=failed_attempts,
                    locked_until=lock_until,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()

            user_response = await UserService.get_user_by_id(db, user_db.id)
            return (user_response, True) if user_response else None

        # Successful login
        await db.execute(
            update(User)
            .where(User.id == UUID(user_db.id))
            .values(
                failed_login_attempts=0,
                locked_until=None,
                last_login_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()

        user_response = await UserService.get_user_by_id(db, user_db.id)
        return (user_response, False) if user_response else None

    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[UserResponse]:
        """
        Get list of users with optional filtering.

        Args:
            db: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return
            role: Filter by role
            status: Filter by status

        Returns:
            List of UserResponse
        """
        query = select(User)

        # Apply filters
        if role:
            try:
                query = query.where(User.role == UserRole(role))
            except ValueError:
                pass

        if status:
            try:
                query = query.where(User.status == UserStatus(status))
            except ValueError:
                pass

        # Add pagination and ordering
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        users = result.scalars().all()

        return [
            UserResponse(
                id=str(user.id),
                email=user.email,
                role=user.role.value,
                status=user.status.value,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]

    @staticmethod
    async def count_users(
        db: AsyncSession,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Count users with optional filtering.

        Args:
            db: Database session
            role: Filter by role
            status: Filter by status

        Returns:
            Number of users
        """
        query = select(func.count(User.id))

        # Apply filters
        if role:
            try:
                query = query.where(User.role == UserRole(role))
            except ValueError:
                pass

        if status:
            try:
                query = query.where(User.status == UserStatus(status))
            except ValueError:
                pass

        result = await db.execute(query)
        return result.scalar()
