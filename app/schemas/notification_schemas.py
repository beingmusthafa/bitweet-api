from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class NotificationBase(BaseModel):
    title: Optional[str] = None
    message: str

class NotificationCreate(NotificationBase):
    user_id: str

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool

class WebSocketMessage(BaseModel):
    type: str  # "notification", "unread_notifications", "error"
    data: dict

class PaginatedNotificationsResponse(BaseModel):
    data: list[NotificationResponse]
    page: int
    has_more: bool