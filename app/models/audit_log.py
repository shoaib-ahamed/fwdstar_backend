"""
Audit log database model.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Index,
    Text,
    Uuid,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    """
    Audit log model for tracking all authentication-related events.

    Records all important user actions for security and compliance.
    """
    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True
    )

    # Foreign key to user (nullable for system events)
    user_id: Mapped[Optional[str]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID of the user who performed the action"
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action type (e.g., USER_LOGIN, USER_REGISTERED)"
    )

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # Supports IPv6
        nullable=True,
        comment="Client IP address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Client user agent string"
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional action-specific data"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # User relationship
    user = relationship(
        "User",
        back_populates="audit_logs",
        lazy="joined"
    )

    def __repr__(self) -> str:
        """String representation of the AuditLog model."""
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}', created_at={self.created_at})>"
        )


# Database indexes for efficient querying
Index("idx_audit_user_id", AuditLog.user_id)
Index("idx_audit_action", AuditLog.action)
Index("idx_audit_created_at", AuditLog.created_at.desc())
