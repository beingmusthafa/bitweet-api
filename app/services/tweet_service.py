from database.connection import get_db
from typing import Dict, Optional, List

class TweetService:
    @staticmethod
    async def create_tweet(user_id: str, text: str, is_private: bool) -> Dict:
        db = await get_db()
        
        try:
            # Create tweet with user relation included in the response
            tweet = await db.tweet.create(
                data={
                    "text": text,
                    "isPrivate": is_private,
                    "userId": user_id
                },
                include={"user": True}  # Include the user in the response
            )
            
            return tweet
            
        except Exception as e:
            raise ValueError(f"Failed to create tweet: {str(e)}")
        
    @staticmethod
    async def update_tweet(tweet_id: str, user_id: str, text: Optional[str] = None, is_private: Optional[bool] = None) -> Dict:
        db = await get_db()
        
        try:
            # Check if tweet exists and belongs to user
            existing_tweet = await db.tweet.find_unique(where={"id": tweet_id})
            
            if not existing_tweet:
                raise ValueError("Tweet not found")
                
            if existing_tweet.userId != user_id:
                raise ValueError("You can only update your own tweets")
            
            # Prepare update data
            update_data = {}
            if text is not None:
                update_data["text"] = text
            if is_private is not None:
                update_data["isPrivate"] = is_private
            
            # Update tweet
            updated_tweet = await db.tweet.update(
                where={"id": tweet_id},
                data=update_data,
                include={"user": True}  # Include the user in the response
            )
            
            return updated_tweet
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to update tweet: {str(e)}")
    
    @staticmethod
    async def delete_tweet(tweet_id: str, user_id: str) -> Dict:
        db = await get_db()
        
        try:
            # Check if tweet exists and belongs to user
            existing_tweet = await db.tweet.find_unique(where={"id": tweet_id})
            
            if not existing_tweet:
                raise ValueError("Tweet not found")
                
            if existing_tweet.userId != user_id:
                raise ValueError("You can only delete your own tweets")
            
            # Delete tweet
            await db.tweet.delete(where={"id": tweet_id})
            
            return {"message": "Tweet deleted successfully"}
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to delete tweet: {str(e)}")
    
    @staticmethod
    async def get_user_tweets(user_id: str, page_number: int = 1, page_size: int = 10) -> Dict:
        db = await get_db()
        
        try:
            # Calculate skip for pagination
            skip = (page_number - 1) * page_size
            
            # Get user tweets with pagination, ordered by creation date (newest first)
            tweets = await db.tweet.find_many(
                where={"userId": user_id},
                skip=skip,
                take=page_size,
                order={"createdAt": "desc"},
                include={"user": True}
            )
            
            # Get total count for pagination
            total_count = await db.tweet.count(where={"userId": user_id})
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
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
        db = await get_db()
        
        try:
            # Calculate skip for pagination
            skip = (page_number - 1) * page_size
            
            # Define the where condition for timeline tweets
            where_condition = {
                "OR": [
                    # Public tweets from any user except current user
                    {"isPrivate": False, "userId": {"not": current_user_id}},
                    
                    # Private tweets from users that the current user follows
                    {
                        "isPrivate": True,
                        "userId": {"not": current_user_id},
                        "user": {
                            "followers": {
                                "some": {
                                    "followerId": current_user_id
                                }
                            }
                        }
                    }
                ]
            }
            
            # Use Prisma's relational queries to directly filter tweets
            tweets = await db.tweet.find_many(
                where=where_condition,
                skip=skip,
                take=page_size,
                order={"createdAt": "desc"},
                include={"user": True}  # Join with user table to get user details
            )
            
            # Get total count for pagination
            total_count = await db.tweet.count(where=where_condition)
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
            return {
                "tweets": tweets,
                "page": page_number,
                "page_size": page_size,
                "total": total_count,
                "total_pages": total_pages
            }
            
        except Exception as e:
            raise ValueError(f"Failed to fetch timeline tweets: {str(e)}")