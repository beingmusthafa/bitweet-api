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
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        # Store connection in memory
        self.active_connections[connection_id] = websocket
        
        # Store user-connection mapping in Redis
        if self.redis_client:
            try:
                await self.redis_client.set(f"user:{user_id}", connection_id, ex=3600)  # 1 hour expiry
            except Exception as e:
                print(f"Failed to store user connection in Redis: {e}")
        
        return connection_id
    
    async def disconnect(self, connection_id: str, user_id: str):
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(f"user:{user_id}")
            except Exception as e:
                print(f"Failed to remove user connection from Redis: {e}")
    
    async def send_message(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                # Connection is broken, clean it up
                del self.active_connections[connection_id]
                return False
        return False
    
    async def send_message_to_user(self, user_id: str, message: dict) -> bool:
        if not self.redis_client:
            return False
            
        try:
            # Get connection_id for user from Redis
            connection_id = await self.redis_client.get(f"user:{user_id}")
            if connection_id:
                return await self.send_message(connection_id, message)
        except Exception as e:
            print(f"Failed to get user connection from Redis: {e}")
        return False
    
    async def is_user_connected(self, user_id: str) -> bool:
        if not self.redis_client:
            return False
        try:
            connection_id = await self.redis_client.get(f"user:{user_id}")
            return connection_id is not None and connection_id in self.active_connections
        except Exception as e:
            print(f"Failed to check user connection in Redis: {e}")
            return False
    
    async def get_connection_count(self) -> int:
        return len(self.active_connections)

# Global instance
websocket_manager = WebSocketManager()