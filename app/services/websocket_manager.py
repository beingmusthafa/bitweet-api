from fastapi import WebSocket
import redis.asyncio as redis
import json
import uuid
from typing import Dict, Optional
import os

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = None

    async def init_redis(self):
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = os.getenv("REDIS_PORT", "6379")
            redis_url = os.getenv("REDIS_URL", f"redis://{redis_host}:{redis_port}")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await self.redis_client.ping()
            print(f"Redis connected successfully at {redis_url}")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        print(f"🔌 [WEBSOCKET] Accepting WebSocket connection for user {user_id}")
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        print(f"🆔 [WEBSOCKET] Generated connection_id: {connection_id}")

        # Store connection in memory
        self.active_connections[connection_id] = websocket
        print(f"💾 [WEBSOCKET] Stored connection in memory. Total connections: {len(self.active_connections)}")

        # Store user-connection mapping in Redis
        if self.redis_client:
            try:
                await self.redis_client.set(f"user:{user_id}", connection_id, ex=3600)  # 1 hour expiry
                print(f"✅ [WEBSOCKET] Stored user-connection mapping in Redis: user:{user_id} -> {connection_id}")
            except Exception as e:
                print(f"❌ [WEBSOCKET] Failed to store user connection in Redis: {e}")
        else:
            print(f"⚠️ [WEBSOCKET] Redis client not available, connection mapping not stored")

        return connection_id

    async def disconnect(self, connection_id: str, user_id: str):
        print(f"🔌 [WEBSOCKET] Disconnecting user {user_id} with connection_id {connection_id}")
        
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            print(f"💾 [WEBSOCKET] Removed connection from memory. Remaining connections: {len(self.active_connections)}")
        else:
            print(f"⚠️ [WEBSOCKET] Connection {connection_id} not found in active connections")

        # Remove from Redis
        if self.redis_client:
            try:
                result = await self.redis_client.delete(f"user:{user_id}")
                print(f"✅ [WEBSOCKET] Removed user mapping from Redis. Keys deleted: {result}")
            except Exception as e:
                print(f"❌ [WEBSOCKET] Failed to remove user connection from Redis: {e}")
        else:
            print(f"⚠️ [WEBSOCKET] Redis client not available for cleanup")

    async def send_message(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
                print("Notification sent : ", message)
                return True
            except Exception as e:
                # Connection is broken, clean it up
                del self.active_connections[connection_id]
                return False
        return False

    async def send_message_to_user(self, user_id: str, message: dict) -> bool:
        print(f"📡 [WEBSOCKET] Attempting to send message to user {user_id}")
        if not self.redis_client:
            print(f"❌ [WEBSOCKET] Redis client not available")
            return False

        try:
            print(f"🔍 [WEBSOCKET] Looking up connection_id for user {user_id} in Redis")
            # Get connection_id for user from Redis
            connection_id = await self.redis_client.get(f"user:{user_id}")
            print(f"🔑 [WEBSOCKET] Found connection_id: {connection_id}")
            if connection_id:
                print(f"📤 [WEBSOCKET] Sending message via connection {connection_id}")
                result = await self.send_message(connection_id, message)
                print(f"✅ [WEBSOCKET] Message send result: {result}")
                return result
            else:
                print(f"📵 [WEBSOCKET] No connection_id found for user {user_id}")
        except Exception as e:
            print(f"❌ [WEBSOCKET] Failed to get user connection from Redis: {e}")
        return False

    async def is_user_connected(self, user_id: str) -> bool:
        print(f"🔍 [WEBSOCKET] Checking if user {user_id} is connected")
        debug_info = await self.debug_user_connection(user_id)
        print(f"🔍 [WEBSOCKET] Debug info: {debug_info}")
        
        if not self.redis_client:
            print(f"❌ [WEBSOCKET] Redis client not available for connection check")
            return False
        try:
            connection_id = await self.redis_client.get(f"user:{user_id}")
            is_connected = connection_id is not None and connection_id in self.active_connections
            print(f"📡 [WEBSOCKET] User {user_id} connection status: connection_id={connection_id}, is_connected={is_connected}")
            return is_connected
        except Exception as e:
            print(f"❌ [WEBSOCKET] Failed to check user connection in Redis: {e}")
            return False

    async def get_connection_count(self) -> int:
        return len(self.active_connections)
    
    async def debug_user_connection(self, user_id: str) -> dict:
        """Debug method to check user connection status in both memory and Redis"""
        debug_info = {
            "user_id": user_id,
            "redis_available": self.redis_client is not None,
            "total_active_connections": len(self.active_connections),
            "connection_id_in_redis": None,
            "connection_exists_in_memory": False
        }
        
        if self.redis_client:
            try:
                connection_id = await self.redis_client.get(f"user:{user_id}")
                debug_info["connection_id_in_redis"] = connection_id
                if connection_id:
                    debug_info["connection_exists_in_memory"] = connection_id in self.active_connections
            except Exception as e:
                debug_info["redis_error"] = str(e)
        
        return debug_info

# Global instance
websocket_manager = WebSocketManager()
