from database.connection import AsyncSessionLocal
from database.models import Tweet, User
from utils.security_middleware import sanitize_string
from typing import Dict, Optional, List
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.orm import selectinload

class TweetService:
    @staticmethod
    async def create_tweet(user_id: str, text: str, is_private: bool) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Sanitize tweet text
                sanitized_text = sanitize_string(text)
                
                # Create tweet
                tweet = Tweet(
                    text=sanitized_text,
                    isPrivate=is_private,
                    userId=user_id
                )
                db.add(tweet)
                await db.commit()
                await db.refresh(tweet)
                
                # Load user relationship
                result = await db.execute(
                    select(Tweet).options(selectinload(Tweet.user)).where(Tweet.id == tweet.id)
                )
                tweet_with_user = result.scalar_one()
                
                return {
                    "id": str(tweet_with_user.id),
                    "text": tweet_with_user.text,
                    "isPrivate": tweet_with_user.isPrivate,
                    "createdAt": tweet_with_user.createdAt,
                    "userId": str(tweet_with_user.userId),
                    "user": {
                        "id": str(tweet_with_user.user.id),
                        "email": tweet_with_user.user.email,
                        "username": tweet_with_user.user.username,
                        "fullName": tweet_with_user.user.fullName
                    } if tweet_with_user.user else None
                }
                
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to create tweet: {str(e)}")
        
    @staticmethod
    async def update_tweet(tweet_id: str, user_id: str, text: Optional[str] = None, is_private: Optional[bool] = None) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Check if tweet exists and belongs to user
                result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
                existing_tweet = result.scalar_one_or_none()
                
                if not existing_tweet:
                    raise ValueError("Tweet not found")
                    
                if str(existing_tweet.userId) != user_id:
                    raise ValueError("You can only update your own tweets")
                
                # Prepare update data
                update_data = {}
                if text is not None:
                    update_data["text"] = sanitize_string(text)
                if is_private is not None:
                    update_data["isPrivate"] = is_private
                
                # Update tweet using SQLAlchemy update
                if update_data:
                    await db.execute(
                        update(Tweet)
                        .where(Tweet.id == tweet_id)
                        .values(**update_data)
                    )
                    await db.commit()
                
                # Load updated tweet with user relationship
                result = await db.execute(
                    select(Tweet).options(selectinload(Tweet.user)).where(Tweet.id == tweet_id)
                )
                updated_tweet = result.scalar_one()
                
                return {
                    "id": str(updated_tweet.id),
                    "text": updated_tweet.text,
                    "isPrivate": updated_tweet.isPrivate,
                    "createdAt": updated_tweet.createdAt,
                    "userId": str(updated_tweet.userId),
                    "user": {
                        "id": str(updated_tweet.user.id),
                        "email": updated_tweet.user.email,
                        "username": updated_tweet.user.username,
                        "fullName": updated_tweet.user.fullName
                    } if updated_tweet.user else None
                }
                
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to update tweet: {str(e)}")
    
    @staticmethod
    async def delete_tweet(tweet_id: str, user_id: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Check if tweet exists and belongs to user
                result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
                existing_tweet = result.scalar_one_or_none()
                
                if not existing_tweet:
                    raise ValueError("Tweet not found")
                    
                if str(existing_tweet.userId) != user_id:
                    raise ValueError("You can only delete your own tweets")
                
                # Delete tweet using SQLAlchemy delete
                await db.execute(
                    delete(Tweet).where(Tweet.id == tweet_id)
                )
                await db.commit()
                
                return {"message": "Tweet deleted successfully"}
                
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to delete tweet: {str(e)}")
    
    @staticmethod
    async def get_user_tweets(user_id: str, page_number: int = 1, page_size: int = 10) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Calculate skip for pagination
                skip = (page_number - 1) * page_size
                
                # Get user tweets with pagination, ordered by creation date (newest first)
                result = await db.execute(
                    select(Tweet)
                    .options(selectinload(Tweet.user))
                    .where(Tweet.userId == user_id)
                    .order_by(Tweet.createdAt.desc())
                    .offset(skip)
                    .limit(page_size)
                )
                tweets_raw = result.scalars().all()
                
                # Convert to dict format
                tweets = [{
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "isPrivate": tweet.isPrivate,
                    "createdAt": tweet.createdAt,
                    "userId": str(tweet.userId),
                    "user": {
                        "id": str(tweet.user.id),
                        "email": tweet.user.email,
                        "username": tweet.user.username,
                        "fullName": tweet.user.fullName
                    } if tweet.user else None
                } for tweet in tweets_raw]
                
                # Get total count for pagination
                count_result = await db.execute(
                    select(func.count(Tweet.id)).where(Tweet.userId == user_id)
                )
                total_count = count_result.scalar() or 0
                total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
                
                return {
                    "tweets": tweets,
                    "page": page_number,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": total_pages
                }
                
            except Exception as e:
                raise ValueError(f"Failed to fetch user tweets: {str(e)}")
    
    @staticmethod
    async def get_timeline_tweets(current_user_id: str, page_number: int = 1, page_size: int = 10) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                from database.models import Follow
                
                # Calculate skip for pagination
                skip = (page_number - 1) * page_size
                
                # Define the where condition for timeline tweets using SQLAlchemy
                # Public tweets from any user except current user OR
                # Private tweets from users that the current user follows
                where_condition = or_(
                    # Public tweets from any user except current user
                    and_(Tweet.isPrivate == False, Tweet.userId != current_user_id),
                    
                    # Private tweets from users that the current user follows
                    and_(
                        Tweet.isPrivate == True,
                        Tweet.userId != current_user_id,
                        Tweet.userId.in_(
                            select(Follow.followingId).where(Follow.followerId == current_user_id)
                        )
                    )
                )
                
                # Get tweets with user details
                result = await db.execute(
                    select(Tweet)
                    .options(selectinload(Tweet.user))
                    .where(where_condition)
                    .order_by(Tweet.createdAt.desc())
                    .offset(skip)
                    .limit(page_size)
                )
                tweets_raw = result.scalars().all()

                tweets = [
                    {
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "createdAt": tweet.createdAt,
                        "isPrivate": tweet.isPrivate,
                        "user": {
                            "id": str(tweet.user.id),
                            "fullName": tweet.user.fullName,
                            "username": tweet.user.username
                        } if tweet.user else None
                    }
                    for tweet in tweets_raw
                ]
                            
                # Get total count for pagination
                count_result = await db.execute(
                    select(func.count(Tweet.id)).where(where_condition)
                )
                total_count = count_result.scalar() or 0
                total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
                
                return {
                    "tweets": tweets,
                    "page": page_number,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": total_pages
                }
                
            except Exception as e:
                raise ValueError(f"Failed to fetch timeline tweets: {str(e)}")