"""
User database model.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    Integer,
    Index,
    Text,
    Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(PyEnum):
    """User roles in the system."""
    SHIPPER = "SHIPPER"
    CARRIER_OWNER = "CARRIER_OWNER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"


class UserStatus(PyEnum):
    """User account status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class User(Base):
    """
    User model for authentication and authorization.

    Stores user credentials, role, and security-related fields.
    """
    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True
    )

    # Credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User email address (unique)"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )

    # Role and status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False,
        index=True,
        comment="User role in the system"
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False),
        default=UserStatus.ACTIVE,
        nullable=False,
        comment="Account status"
    )

    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of consecutive failed login attempts"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account locked until this timestamp"
    )

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Audit logs relationship
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of the User model."""
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"role={self.role.value}, status={self.status.value})>"
        )


# Database indexes for performance
Index("idx_users_email", User.email)
Index("idx_users_role", User.role)
Index("idx_users_status", User.status)
Index("idx_users_locked_until", User.locked_until)
