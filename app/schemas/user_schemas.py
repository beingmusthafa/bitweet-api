from pydantic import BaseModel
from typing import List

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