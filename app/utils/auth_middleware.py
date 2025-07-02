from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.token_utils import verify_token
from database.connection import get_db

security = HTTPBearer()

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # First check for token in Authorization header
        token = credentials.credentials
    except:
        # If not in header, try to get from cookies
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Verify the token
        payload = await verify_token(token)
        if payload["type"] != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Get user from database
        db = await get_db()
        user = await db.user.find_unique(where={"id": payload["user_id"]})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Exclude password from user object
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "fullName": user.fullName
        }
        
        return user_dict
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")