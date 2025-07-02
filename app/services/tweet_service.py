from database.connection import get_db
from typing import Dict, Optional

class TweetService:
    @staticmethod
    async def create_tweet(user_id: str, text: str, is_private: bool) -> Dict:
        db = await get_db()
        
        try:
            tweet = await db.tweet.create(
                data={
                    "text": text,
                    "isPrivate": is_private,
                    "userId": user_id
                }
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
                data=update_data
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