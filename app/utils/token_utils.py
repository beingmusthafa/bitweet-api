import jwt
from datetime import datetime, timedelta
from typing import Dict
import os
from database.connection import AsyncSessionLocal
from database.models import BlacklistedToken
from sqlalchemy import select

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def generate_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_tokens(user_id: str) -> Dict[str, str]:
    return {
        "access_token": generate_access_token(user_id),
        "refresh_token": generate_refresh_token(user_id)
    }

async def is_token_blacklisted(token: str) -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BlacklistedToken).where(BlacklistedToken.token == token)
        )
        blacklisted = result.scalar_one_or_none()
        return blacklisted is not None

async def verify_token(token: str) -> Dict:
    try:
        # Check if token is blacklisted
        if await is_token_blacklisted(token):
            raise ValueError("Token has been revoked")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ [TOKEN] SUCCESS - Token decoded successfully")
        print(f"🔐 [TOKEN] Payload: user_id={payload.get('user_id')}, type={payload.get('type')}, exp={payload.get('exp')}")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ [TOKEN] FAILED - Invalid token: {str(e)}")
        raise ValueError("Invalid token")
    except Exception as e:
        print(f"❌ [TOKEN] FAILED - Unexpected error during token verification: {str(e)}")
        raise ValueError(f"Token verification failed: {str(e)}")
