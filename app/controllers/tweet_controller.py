from fastapi import APIRouter, HTTPException, Depends, Request, Path, Query
from pydantic import ValidationError
from schemas.tweet_schemas import TweetRequest, TweetResponse
from services.tweet_service import TweetService
from utils.auth_middleware import get_current_user
from typing import Dict, List

router = APIRouter(prefix="/user/tweets", tags=["Tweets"])

@router.post("/", response_model=TweetResponse)
async def create_tweet(request: Request, current_user: Dict = Depends(get_current_user)):
    try:
        body = await request.json()
        tweet_data = TweetRequest(**body)
        
        # Call service layer with authenticated user ID
        result = await TweetService.create_tweet(
            user_id=current_user["id"],
            text=tweet_data.text,
            is_private=tweet_data.isPrivate
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

@router.put("/{tweet_id}", response_model=TweetResponse)
async def update_tweet(
    request: Request, 
    tweet_id: str = Path(..., title="The ID of the tweet to update"),
    current_user: Dict = Depends(get_current_user)
):
    try:
        body = await request.json()
        tweet_data = TweetRequest(**body)
        
        # Call service layer with authenticated user ID
        result = await TweetService.update_tweet(
            tweet_id=tweet_id,
            user_id=current_user["id"],
            text=tweet_data.text,
            is_private=tweet_data.isPrivate
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

@router.delete("/{tweet_id}")
async def delete_tweet(
    tweet_id: str = Path(..., title="The ID of the tweet to delete"),
    current_user: Dict = Depends(get_current_user)
):
    try:
        # Call service layer with authenticated user ID
        result = await TweetService.delete_tweet(
            tweet_id=tweet_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/my-tweets", response_model=List[TweetResponse])
async def get_my_tweets(
    page_number: int = Query(1, ge=1, description="Page number for pagination"),
    current_user: Dict = Depends(get_current_user)
):
    try:
        # Call service layer to get current user's tweets
        tweets = await TweetService.get_user_tweets(
            user_id=current_user["id"],
            page_number=page_number
        )
        
        return tweets
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[TweetResponse])
async def get_timeline(
    page_number: int = Query(1, ge=1, description="Page number for pagination"),
    current_user: Dict = Depends(get_current_user)
):
    try:
        # Call service layer to get timeline tweets
        tweets = await TweetService.get_timeline_tweets(
            current_user_id=current_user["id"],
            page_number=page_number
        )
        
        return tweets
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")