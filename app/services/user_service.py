from database.connection import get_db
from typing import Dict

class UserService:
    @staticmethod
    async def follow_user(follower_id: str, following_id: str) -> Dict:
        db = await get_db()
        
        try:
            # Check if users exist
            following_user = await db.user.find_unique(where={"id": following_id})
            if not following_user:
                raise ValueError("User to follow does not exist")
                
            if follower_id == following_id:
                raise ValueError("You cannot follow yourself")
            
            # Check if already following
            existing_follow = await db.follow.find_unique(
                where={
                    "followerId_followingId": {
                        "followerId": follower_id,
                        "followingId": following_id
                    }
                }
            )
            
            if existing_follow:
                return {"message": f"You are already following {following_user.username}"}
            
            # Create follow relationship
            await db.follow.create(
                data={
                    "followerId": follower_id,
                    "followingId": following_id
                }
            )
            
            return {"message": f"You are now following {following_user.username}"}
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to follow user: {str(e)}")