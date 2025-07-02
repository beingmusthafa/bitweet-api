from pydantic import BaseModel

class FollowRequest(BaseModel):
    to_follow: str  # User ID to follow