import datetime
from services.notification_service import NotificationService
from services.websocket_manager import websocket_manager
from database.connection import AsyncSessionLocal
from typing import Optional

async def send_notification(user_id: str, message: str, title: Optional[str] = None):
    try:
        if websocket_manager.redis_client is None:
            await websocket_manager.init_redis()

        print(f"🔍 [WEBSOCKET] Checking if user {user_id} is connected via WebSocket")
        # Check if user is connected
        is_connected = await websocket_manager.is_user_connected(user_id)
        print(f"📡 [WEBSOCKET] User {user_id} connection status: {is_connected}")

        if is_connected:
            print(f"💬 [WEBSOCKET] User is connected, preparing real-time notification")
            notification_message = {
                "type": "new_notification",
                "data": {
                    "title": title,
                    "message": message,
                    "created_at": datetime.datetime.now().isoformat()
                }
            }
            print(f"📤 [WEBSOCKET] Sending real-time notification: {notification_message}")
            await websocket_manager.send_message_to_user(user_id, notification_message)
            print(f"✅ [WEBSOCKET] Real-time notification sent successfully")
        else:
            print(f"📵 [WEBSOCKET] User not connected via WebSocket, skipping real-time notification")

        async with AsyncSessionLocal() as db:
            await NotificationService.create_notification(db, user_id, message, title)

    except Exception as e:
        print(f"❌ [WEBSOCKET] Error occurred: {str(e)}")
        async with AsyncSessionLocal() as db:
            await NotificationService.create_notification(db, user_id, message, title)
