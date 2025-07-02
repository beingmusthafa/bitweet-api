from pydantic import BaseModel, EmailStr, validator
import re

class UserRegistrationRequest(BaseModel):
    email: EmailStr
    username: str
    fullName: str
    password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @validator('fullName')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()

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

class UserRegistrationResponse(BaseModel):
    id: str
    email: str
    username: str
    fullName: str
    message: str

class UserLoginRequest(BaseModel):
    identifier: str  # Can be email or username
    password: str

class UserLoginResponse(BaseModel):
    id: str
    email: str
    username: str
    fullName: str
    message: str