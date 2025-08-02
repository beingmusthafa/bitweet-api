import datetime
from services.notification_service import NotificationService
from services.websocket_manager import websocket_manager
from database.connection import AsyncSessionLocal
from typing import Optional

async def send_notification(user_id: str, message: str, title: Optional[str] = None):
    try:
        if websocket_manager.redis_client is None:
            await websocket_manager.init_redis()

        # Check if user is connected
        is_connected = await websocket_manager.is_user_connected(user_id)

        if is_connected:
            notification_message = {
                "type": "notification",
                "data": {
                    "title": title,
                    "message": message,
                    "created_at": datetime.datetime.now().isoformat()
                }
            }

            await websocket_manager.send_message_to_user(user_id, notification_message)
        async with AsyncSessionLocal() as db:
            await NotificationService.create_notification(db, user_id, message, title)

    except Exception as e:
        async with AsyncSessionLocal() as db:
            await NotificationService.create_notification(db, user_id, message, title)
