from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from database.connection import AsyncSessionLocal, get_db
from database.models import Room, Participant, User
from utils.auth_middleware import get_current_user
from utils.token_utils import verify_token
from pydantic import BaseModel
from typing import List, Dict, Set
import json
import hashlib
import hmac
import base64
import time
import os
from typing import Optional

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

# In-memory storage for active WebSocket connections
# room_id -> {user_id: websocket}
active_connections: Dict[str, Dict[str, WebSocket]] = {}

# Pydantic models
class CreateRoomRequest(BaseModel):
    title: str

@router.get("/turn-credentials")
async def get_turn_credentials():
    try:
        turn_server = os.getenv("TURN_SERVER")
        if not turn_server:
            raise HTTPException(status_code=500, detail="TURN server not configured")

        turn_secret = os.getenv("TURN_SECRET")
        if not turn_secret:
            raise HTTPException(status_code=500, detail="TURN server not configured")

        turn_username = os.getenv("TURN_USERNAME")
        if not turn_username:
            raise HTTPException(status_code=500, detail="TURN username not configured")

        return {
            "iceServers": [
                {
                    "urls": ["stun:stun.l.google.com:19302"]
                },
                {
                    "urls": [
                        f"turn:{turn_server}:3478",
                    ],
                    "username": turn_username,
                    "credential": turn_secret
                }
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate credentials")

# REST API Endpoints
@router.post("/")
async def create_room(
    room_data: CreateRoomRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """Create a new audio chat room"""
    try:
        room = Room(
            title=room_data.title,
            host_id=current_user["id"],
            is_live=True  # Rooms are live by default for simplicity
        )

        db.add(room)
        await db.commit()
        await db.refresh(room)

        return {
            "id": str(room.id),
            "title": room.title,
            "is_live": room.is_live,
            "host_id": str(room.host_id),
            "created_at": room.created_at.isoformat()
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")

@router.get("/active")
async def get_active_rooms(db: AsyncSessionLocal = Depends(get_db)):
    """Get all live/active rooms"""
    try:
        result = await db.execute(
            select(Room)
            .options(selectinload(Room.host), selectinload(Room.participants).selectinload(Participant.user))
            .where(Room.is_live == True)
            .order_by(Room.created_at.desc())
        )
        rooms = result.scalars().all()

        rooms_data = []
        for room in rooms:
            # Count active WebSocket connections for this room
            active_count = len(active_connections.get(str(room.id), {}))

            rooms_data.append({
                "id": str(room.id),
                "title": room.title,
                "is_live": room.is_live,
                "host_id": str(room.host_id),
                "created_at": room.created_at.isoformat(),
                "host": {
                    "id": str(room.host.id),
                    "username": room.host.username,
                    "fullName": room.host.fullName
                },
                "active_participants": active_count
            })

        return {"rooms": rooms_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active rooms: {str(e)}")

@router.get("/{room_id}")
async def get_room(room_id: str, db: AsyncSessionLocal = Depends(get_db)):
    """Get room details"""
    try:
        result = await db.execute(
            select(Room)
            .options(selectinload(Room.host))
            .where(Room.id == room_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Get active participants from WebSocket connections
        active_users = list(active_connections.get(room_id, {}).keys())

        return {
            "id": str(room.id),
            "title": room.title,
            "is_live": room.is_live,
            "host_id": str(room.host_id),
            "created_at": room.created_at.isoformat(),
            "host": {
                "id": str(room.host.id),
                "username": room.host.username,
                "fullName": room.host.fullName
            },
            "active_participants": len(active_users)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch room: {str(e)}")

@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """Delete a room (host only)"""
    try:
        result = await db.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if str(room.host_id) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Only the room host can delete the room")

        # Disconnect all users from the room
        if room_id in active_connections:
            for user_id, websocket in active_connections[room_id].items():
                try:
                    await websocket.send_text(json.dumps({
                        "type": "room_deleted",
                        "message": "Room has been deleted by the host"
                    }))
                    await websocket.close()
                except:
                    pass
            del active_connections[room_id]

        await db.delete(room)
        await db.commit()

        return {"message": "Room deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")

# WebSocket Authentication Helper
async def authenticate_websocket(websocket: WebSocket) -> dict:
    """Authenticate WebSocket connection using JWT token from cookies"""
    try:
        # Get token from cookies
        cookies = websocket.cookies
        token = cookies.get("access_token")

        if not token:
            return None

        payload = await verify_token(token)
        if payload["type"] != "access":
            return None

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == payload["user_id"]))
            user = result.scalar_one_or_none()

            if not user:
                return None

            return {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "fullName": user.fullName
            }
    except Exception:
        return None

# WebSocket Helper Functions
async def broadcast_to_room(room_id: str, message: dict, exclude_user_id: str = None):
    """Broadcast message to all users in a room"""
    if room_id not in active_connections:
        return

    disconnected_users = []
    for user_id, websocket in active_connections[room_id].items():
        if exclude_user_id and user_id == exclude_user_id:
            continue

        try:
            await websocket.send_text(json.dumps(message))
        except:
            disconnected_users.append(user_id)

    # Clean up disconnected users
    for user_id in disconnected_users:
        active_connections[room_id].pop(user_id, None)
        if not active_connections[room_id]:
            del active_connections[room_id]

# WebSocket Endpoint
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for audio room"""
    print(f"🔌 [CONNECT] New WebSocket connection attempt for room {room_id}")
    await websocket.accept()
    print(f"🔌 [CONNECT] WebSocket accepted for room {room_id}")

    # Authenticate user
    user = await authenticate_websocket(websocket)
    if not user:
        print(f"❌ [CONNECT] Authentication failed for room {room_id}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Authentication failed. Please login and try again.",
            "code": "AUTH_FAILED"
        }))
        await websocket.close()
        print(f"🔌 [DISCONNECT] Connection closed due to auth failure for room {room_id}")
        return

    print(f"✅ [CONNECT] User {user['username']} authenticated for room {room_id}")

    # Verify room exists
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()

        if not room:
            print(f"❌ [CONNECT] Room {room_id} not found for user {user['username']}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Room not found",
                "code": "ROOM_NOT_FOUND"
            }))
            await websocket.close()
            print(f"🔌 [DISCONNECT] Connection closed due to room not found for user {user['username']}")
            return

        if not room.is_live:
            print(f"❌ [CONNECT] Room {room_id} is not live for user {user['username']}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Room is not live",
                "code": "ROOM_NOT_LIVE"
            }))
            await websocket.close()
            print(f"🔌 [DISCONNECT] Connection closed due to room not live for user {user['username']}")
            return

    # Add user to room connections
    if room_id not in active_connections:
        active_connections[room_id] = {}

    active_connections[room_id][user["id"]] = websocket
    print(f"✅ [CONNECT] User {user['username']} successfully connected to room {room_id}")
    print(f"📊 [CONNECT] Room {room_id} now has {len(active_connections[room_id])} active connections")

    # Get existing participants with their profile data
    existing_participants = []
    if room_id in active_connections:
        for existing_user_id, _ in active_connections[room_id].items():
            if existing_user_id != user["id"]:  # Exclude the current user
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).where(User.id == existing_user_id))
                    existing_user = result.scalar_one_or_none()
                    if existing_user:
                        existing_participants.append({
                            "id": str(existing_user.id),
                            "username": existing_user.username,
                            "fullName": existing_user.fullName,
                            "email": existing_user.email
                        })

    # Send connection success message with existing participants
    await websocket.send_text(json.dumps({
        "type": "connected",
        "room_id": room_id,
        "user_id": user["id"],
        "username": user["username"],
        "message": "Successfully connected to room",
        "existing_participants": existing_participants
    }))

    # Notify other users with full profile data
    await broadcast_to_room(room_id, {
        "type": "user_joined",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "fullName": user["fullName"],
            "email": user["email"]
        },
        "room_id": room_id
    }, exclude_user_id=user["id"])

    print(f"📢 [CONNECT] Notified other users about {user['username']} joining room {room_id}")

    try:
        print(f"🔄 [LOOP] Starting message loop for user {user['username']} in room {room_id}")
        # Message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "webrtc_signal":
                # Forward WebRTC signaling messages
                target_user_id = message.get("target_user_id")

                if target_user_id and target_user_id in active_connections.get(room_id, {}):
                    # Send to specific user
                    target_websocket = active_connections[room_id][target_user_id]
                    await target_websocket.send_text(json.dumps({
                        "type": "webrtc_signal",
                        "from_user_id": user["id"],
                        "signal_type": message.get("signal_type"),
                        "data": message.get("data")
                    }))
                else:
                    # Broadcast to all other users (for offers)
                    await broadcast_to_room(room_id, {
                        "type": "webrtc_signal",
                        "from_user_id": user["id"],
                        "signal_type": message.get("signal_type"),
                        "data": message.get("data")
                    }, exclude_user_id=user["id"])

            elif message_type == "chat":
                # Handle chat messages - include sender for delivery confirmation
                chat_response = {
                    "type": "chat",
                    "room_id": room_id,
                    "user_id": user["id"],
                    "username": user["username"],
                    "message": message.get("message", ""),
                    "timestamp": message.get("timestamp")
                }

                # Include temp_id if provided by client for message tracking
                if message.get("temp_id"):
                    chat_response["temp_id"] = message.get("temp_id")

                await broadcast_to_room(room_id, chat_response)  # Include sender for delivery confirmation

    except WebSocketDisconnect:
        print(f"🔌 [DISCONNECT] WebSocketDisconnect - User {user['username']} disconnected from room {room_id} (CLIENT INITIATED)")
    except Exception as e:
        print(f"❌ [ERROR] WebSocket error for user {user['username']} in room {room_id}: {str(e)} (SERVER ERROR)")
        print(f"❌ [ERROR] Exception type: {type(e).__name__}")
    finally:
        print(f"🧹 [CLEANUP] Starting cleanup for user {user['username']} in room {room_id}")

        # Clean up connection
        if room_id in active_connections and user["id"] in active_connections[room_id]:
            del active_connections[room_id][user["id"]]
            print(f"🧹 [CLEANUP] Removed {user['username']} from active connections")

            # Clean up empty rooms
            if not active_connections[room_id]:
                del active_connections[room_id]
                print(f"🧹 [CLEANUP] Removed empty room {room_id} from active connections")
            else:
                print(f"📊 [CLEANUP] Room {room_id} now has {len(active_connections[room_id])} active connections")

        # Notify other users with full profile data
        await broadcast_to_room(room_id, {
            "type": "user_left",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "fullName": user["fullName"],
                "email": user["email"]
            },
            "room_id": room_id
        }, exclude_user_id=user["id"])

        print(f"📢 [CLEANUP] Notified other users about {user['username']} leaving room {room_id}")
        print(f"✅ [DISCONNECT] Cleanup completed for user {user['username']} in room {room_id}")
