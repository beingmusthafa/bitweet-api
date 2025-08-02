from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.notification_service import NotificationService
from services.websocket_manager import websocket_manager
from utils.token_utils import verify_token
from utils.auth_middleware import get_current_user
from schemas.notification_schemas import NotificationResponse, WebSocketMessage, PaginatedNotificationsResponse
import json
import uuid
from typing import List, Dict

router = APIRouter(prefix="/notifications", tags=["notifications"])

async def get_user_from_token(token: str) -> str:
    try:
        payload = await verify_token(token)
        return payload.get("user_id")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    connection_id = None
    user_id = None
    
    try:
        # Get token before accepting connection
        token = websocket.cookies.get("access_token")
        if not token:
            await websocket.close(code=1008, reason="No access token found in cookies")
            return

        user_id = await get_user_from_token(token)
        print(f"🔌 [WEBSOCKET] User {user_id} attempting to connect")

        # Initialize Redis if needed
        if websocket_manager.redis_client is None:
            await websocket_manager.init_redis()

        # Use the websocket_manager connect method
        connection_id = await websocket_manager.connect(websocket, user_id)
        print(f"✅ [WEBSOCKET] User {user_id} connected with connection_id: {connection_id}")

        # Send unread notifications
        unread_notifications = await NotificationService.get_unread_notifications(db, user_id)
        notifications_data = [
            {
                "id": str(notif.id),
                "title": notif.title,
                "message": notif.message,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat()
            }
            for notif in unread_notifications
        ]

        welcome_message = {
            "type": "unread_notifications",
            "data": {
                "notifications": notifications_data,
                "count": len(notifications_data)
            }
        }

        await websocket_manager.send_message(connection_id, welcome_message)
        print(f"📋 [WEBSOCKET] Sent {len(notifications_data)} unread notifications to user {user_id}")

        # Keep connection alive by listening for messages
        while True:
            try:
                # Wait for client messages (heartbeat, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                print(f"📨 [WEBSOCKET] Received message from user {user_id}: {message}")
                
                # Handle different message types if needed
                if message.get("type") == "ping":
                    await websocket_manager.send_message(connection_id, {"type": "pong"})
                    
            except WebSocketDisconnect:
                print(f"🔌 [WEBSOCKET] User {user_id} disconnected")
                break
            except json.JSONDecodeError:
                print(f"⚠️ [WEBSOCKET] Invalid JSON from user {user_id}")
            except Exception as e:
                print(f"❌ [WEBSOCKET] Error handling message from user {user_id}: {e}")
                break

    except HTTPException as e:
        print(f"❌ [WEBSOCKET] HTTP error for user {user_id}: {e.detail}")
        await websocket.close(code=1008, reason=e.detail)
    except WebSocketDisconnect:
        print(f"🔌 [WEBSOCKET] User {user_id} disconnected during setup")
    except Exception as e:
        print(f"❌ [WEBSOCKET] Unexpected error for user {user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        if user_id and connection_id:
            print(f"🔌 [WEBSOCKET] Cleaning up connection for user {user_id}")
            await websocket_manager.disconnect(connection_id, user_id)

@router.get("/", response_model=PaginatedNotificationsResponse)
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number starting from 1"),
    limit: int = Query(10, ge=1, le=100, description="Number of notifications per page"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notifications, has_more = await NotificationService.get_paginated_notifications(
        db, current_user["id"], page, limit
    )
    return PaginatedNotificationsResponse(
        data=notifications,
        page=page,
        has_more=has_more
    )

@router.get("/unread", response_model=List[NotificationResponse])
async def get_unread_notifications(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notifications = await NotificationService.get_unread_notifications(db, current_user["id"])
    return notifications

@router.patch("/mark-all-read")
async def mark_all_notifications_read(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    count = await NotificationService.mark_all_notifications_as_read(db, current_user["id"])
    return {"message": f"Marked {count} notifications as read"}
