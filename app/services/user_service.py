from database.connection import get_db
from typing import Dict, List

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
            existing_follow = await db.follow.find_first(
                where={
                    "AND": [
                        {"followerId": follower_id},
                        {"followingId": following_id}
                    ]
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
            
    @staticmethod
    async def unfollow_user(follower_id: str, following_id: str) -> Dict:
        db = await get_db()
        
        try:
            # Check if users exist
            following_user = await db.user.find_unique(where={"id": following_id})
            if not following_user:
                raise ValueError("User to unfollow does not exist")
                
            if follower_id == following_id:
                raise ValueError("You cannot unfollow yourself")
            
            # Check if already following
            existing_follow = await db.follow.find_first(
                where={
                    "AND": [
                        {"followerId": follower_id},
                        {"followingId": following_id}
                    ]
                }
            )
            
            if not existing_follow:
                return {"message": f"You are not following {following_user.username}"}
            
            # Delete follow relationship
            await db.follow.delete(
                where={
                    "followerId_followingId": {
                        "followerId": follower_id,
                        "followingId": following_id
                    }
                }
            )
            
            return {"message": f"You have unfollowed {following_user.username}"}
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to unfollow user: {str(e)}")

    @staticmethod
    async def get_users_paginated(current_user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        db = await get_db()
        
        try:
            # Calculate skip for pagination
            skip = (page - 1) * page_size
            
            # Get users with pagination, excluding current user
            users = await db.user.find_many(
                where={
                    "id": {"not": current_user_id}
                },
                skip=skip,
                take=page_size,
                order={
                    "id": "asc"  # Sort by ID (oldest first)
                }
            )
            
            # Manually exclude password
            users_without_password = [{
                "id": user.id,
                "username": user.username,
                "fullName": user.fullName,
                "email": user.email
            } for user in users]
            
            # Get total count for pagination info (excluding current user)
            total_count = await db.user.count(
                where={"id": {"not": current_user_id}}
            )
            
            return {
                "users": users_without_password,
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to get users: {str(e)}")