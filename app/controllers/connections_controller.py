from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import ValidationError
from schemas.user_schemas import FollowRequest, UnfollowRequest, PaginatedUsersResponse, FollowersResponse, FollowingResponse
from services.connections_service import ConnectionsService
from utils.auth_middleware import get_current_user
from typing import Dict, Optional

router = APIRouter(prefix="/user/connections", tags=["User relations"])

@router.post("/follow")
async def follow_user(request: Request, current_user: Dict = Depends(get_current_user)):
    try:
        body = await request.json()
        follow_data = FollowRequest(**body)

        # Call service layer with authenticated user ID
        result = await ConnectionsService.follow_user(
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

@router.post("/unfollow")
async def unfollow_user(request: Request, current_user: Dict = Depends(get_current_user)):
    try:
        body = await request.json()
        unfollow_data = UnfollowRequest(**body)

        # Call service layer with authenticated user ID
        result = await ConnectionsService.unfollow_user(
            follower_id=current_user["id"],
            following_id=unfollow_data.to_unfollow
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

@router.get("/people", response_model=PaginatedUsersResponse)
async def get_users(page: Optional[int] = Query(1, ge=1), current_user: Dict = Depends(get_current_user)):
    try:
        result = await ConnectionsService.get_users_paginated(
            current_user_id=current_user["id"],
            page=page if page is not None else 1
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/followers", response_model=FollowersResponse)
async def get_followers(current_user: Dict = Depends(get_current_user)):
    try:
        result = await ConnectionsService.get_followers(current_user["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/following", response_model=FollowingResponse)
async def get_following(current_user: Dict = Depends(get_current_user)):
    try:
        result = await ConnectionsService.get_following(current_user["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
