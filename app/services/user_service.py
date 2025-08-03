import random
import string
import time
import re
from database.connection import AsyncSessionLocal
from database.models import User
from services.auth_service import AuthService
from worker import celery, print_otp_to_console
import redis
import os
from sqlalchemy import select, update
from typing import Optional

# Connect to Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# OTP TTL in seconds (5 minutes)
OTP_TTL = 300

class UserService:
    @staticmethod
    def generate_otp(length=6):
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    async def generate_and_send_otp(user_id: str):
        """Generate OTP, store in Redis, and schedule a task to print it"""
        # Generate a 6-digit OTP
        otp = UserService.generate_otp()
        
        # Store OTP in Redis with TTL
        redis_key = f"password_reset_otp:{user_id}"
        redis_client.set(redis_key, otp, ex=OTP_TTL)
        
        # Schedule task to print OTP after 5 seconds
        celery.send_task('worker.print_otp_to_console', args=[otp, user_id], countdown=5, task_id=f"otp-{user_id}")
        
        return {"success": True}
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password using the same rules as registration"""
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', password):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Password must contain at least one special character')
        return password
    
    @staticmethod
    async def verify_otp_and_change_password(user_id: str, otp: str, new_password: str):
        """Verify OTP and change user password if valid"""
        # Check if OTP exists and is valid
        redis_key = f"password_reset_otp:{user_id}"
        stored_otp = redis_client.get(redis_key)
        
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid or expired OTP")
        
        # Validate the new password
        try:
            UserService.validate_password(new_password)
        except ValueError as e:
            raise ValueError(str(e))
        
        # OTP is valid and password is valid, change password
        async with AsyncSessionLocal() as db:
            try:
                # Get current user to check if new password is same as old one
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if not user:
                    raise ValueError("User not found")
                    
                # Hash the new password
                hashed_password = AuthService.hash_password(new_password)
                
                # Check if new password is same as old password
                if AuthService.verify_password(new_password, str(user.password)):
                    raise ValueError("New password cannot be the same as your current password")
                
                # Update user password using SQLAlchemy update
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(password=hashed_password)
                )
                await db.commit()
                
                # Delete the OTP from Redis
                redis_client.delete(redis_key)
                
                return {"success": True}
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to update password: {str(e)}")