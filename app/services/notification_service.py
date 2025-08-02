from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Notification, User
from typing import List, Optional
import uuid
from datetime import datetime

class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        message: str,
        title: Optional[str] = None
    ) -> Notification:
        notification = Notification(
            user_id=uuid.UUID(user_id),
            message=message,
            title=title
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_unread_notifications(db: AsyncSession, user_id: str) -> List[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == uuid.UUID(user_id))
            .where(Notification.is_read == False)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_notifications(db: AsyncSession, user_id: str) -> List[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == uuid.UUID(user_id))
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def mark_all_notifications_as_read(db: AsyncSession, user_id: str) -> int:
        result = await db.execute(
            update(Notification)
            .where(Notification.user_id == uuid.UUID(user_id))
            .where(Notification.is_read == False)
            .values(is_read=True)
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def get_paginated_notifications(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 10
    ) -> tuple[List[Notification], bool]:
        offset = (page - 1) * limit

        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == uuid.UUID(user_id))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        notifications = result.scalars().all()

        has_more = len(notifications) > limit

        # Return only the requested limit
        return notifications[:limit], has_more
