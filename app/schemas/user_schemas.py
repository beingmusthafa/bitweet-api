from pydantic import BaseModel, Field, validator
from typing import List
import re

class FollowRequest(BaseModel):
    to_follow: str  # User ID to follow

class UnfollowRequest(BaseModel):
    to_unfollow: str  # User ID to unfollow

class UserResponse(BaseModel):
    id: str
    username: str
    fullName: str
    email: str

class PaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

class FollowersResponse(BaseModel):
    followers: List[UserResponse]

class FollowingResponse(BaseModel):
    following: List[UserResponse]

class SendOTPRequest(BaseModel):
    pass  # No fields needed as we'll use the authenticated user's ID

class ChangePasswordRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v