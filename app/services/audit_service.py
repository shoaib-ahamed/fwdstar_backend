"""
Audit logging service.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.audit_log import AuditLog


class AuditService:
    """Service for logging audit events."""

    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: Optional[str],
        action: str,
        request: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            db: Database session
            user_id: User ID (optional for system events)
            action: Action type (e.g., 'USER_LOGIN', 'USER_REGISTERED')
            request: FastAPI request object for extracting IP and user agent
            metadata: Additional event metadata
        """
        # Extract IP address
        ip_address = None
        user_agent = None

        if request:
            # Get client IP (handles proxy headers)
            if hasattr(request, 'client') and request.client:
                ip_address = request.client.host
            elif hasattr(request, 'headers'):
                # Try to get from X-Forwarded-For header
                forwarded_for = request.headers.get('x-forwarded-for')
                if forwarded_for:
                    ip_address = forwarded_for.split(',')[0].strip()
                else:
                    ip_address = request.headers.get('x-real-ip')

            # Get user agent
            user_agent = request.headers.get('user-agent')

        # Create audit log entry
        audit_entry = {
            'user_id': UUID(user_id) if user_id else None,
            'action': action,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata_json': metadata,
            'created_at': datetime.utcnow()
        }

        # Insert into database
        await db.execute(insert(AuditLog).values(**audit_entry))
        await db.commit()

    @staticmethod
    async def get_user_audit_logs(
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of AuditLog entries
        """
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_audit_logs_by_action(
        db: AsyncSession,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """
        Get audit logs by action type.

        Args:
            db: Database session
            action: Action type to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of AuditLog entries
        """
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_recent_audit_logs(
        db: AsyncSession,
        hours: int = 24,
        limit: int = 1000
    ) -> list[AuditLog]:
        """
        Get recent audit logs.

        Args:
            db: Database session
            hours: Number of hours to look back
            limit: Maximum number of records to return

        Returns:
            List of AuditLog entries
        """
        from sqlalchemy import and_, func

        since = datetime.utcnow() - timedelta(hours=hours)

        result = await db.execute(
            select(AuditLog)
            .where(and_(AuditLog.created_at >= since))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
