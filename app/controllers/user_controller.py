from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import ValidationError
from schemas.user_schemas import FollowRequest
from services.user_service import UserService
from utils.auth_middleware import get_current_user
from typing import Dict

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/follow")
async def follow_user(request: Request, current_user: Dict = Depends(get_current_user)):
    try:
        body = await request.json()
        follow_data = FollowRequest(**body)
        
        # Call service layer with authenticated user ID
        result = await UserService.follow_user(
            follower_id=current_user["id"],
            following_id=follow_data.to_follow
        )
        
        return result
        
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field_name = error['loc'][-1] if error['loc'] else 'unknown'
            errors[field_name] = error['msg']
        raise HTTPException(status_code=400, detail={"errors": errors})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")