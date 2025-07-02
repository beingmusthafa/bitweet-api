from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class TweetRequest(BaseModel):
    text: str
    isPrivate: bool = False
    
    @validator('text')
    def validate_text(cls, v):
        trimmed = v.strip()
        if len(trimmed) < 1:
            raise ValueError('Tweet text must not be empty')
        if len(trimmed) > 280:
            raise ValueError('Tweet text must not exceed 280 characters')
        return trimmed

class UserInfo(BaseModel):
    id: str
    username: str
    fullName: str
    email: str

class TweetResponse(BaseModel):
    id: str
    text: str
    isPrivate: bool
    createdAt: datetime
    userId: str
    user: UserInfo