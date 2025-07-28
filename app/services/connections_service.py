from database.connection import AsyncSessionLocal
from database.models import User, Follow
from typing import Dict, List
from sqlalchemy import select, func, and_, not_, delete

class ConnectionsService:
    @staticmethod
    async def follow_user(follower_id: str, following_id: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Check if users exist
                result = await db.execute(select(User).where(User.id == following_id))
                following_user = result.scalar_one_or_none()
                if not following_user:
                    raise ValueError("User to follow does not exist")
                    
                if follower_id == following_id:
                    raise ValueError("You cannot follow yourself")
                
                # Check if already following
                result = await db.execute(
                    select(Follow).where(
                        and_(
                            Follow.followerId == follower_id,
                            Follow.followingId == following_id
                        )
                    )
                )
                existing_follow = result.scalar_one_or_none()
                
                if existing_follow:
                    return {"message": f"You are already following {following_user.username}"}
                
                # Create follow relationship
                follow = Follow(
                    followerId=follower_id,
                    followingId=following_id
                )
                db.add(follow)
                await db.commit()
                
                return {"message": f"You are now following {following_user.username}"}
                
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to follow user: {str(e)}")
            
    @staticmethod
    async def unfollow_user(follower_id: str, following_id: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Check if users exist
                result = await db.execute(select(User).where(User.id == following_id))
                following_user = result.scalar_one_or_none()
                if not following_user:
                    raise ValueError("User to unfollow does not exist")
                    
                if follower_id == following_id:
                    raise ValueError("You cannot unfollow yourself")
                
                # Check if already following
                result = await db.execute(
                    select(Follow).where(
                        and_(
                            Follow.followerId == follower_id,
                            Follow.followingId == following_id
                        )
                    )
                )
                existing_follow = result.scalar_one_or_none()
                
                if not existing_follow:
                    return {"message": f"You are not following {following_user.username}"}
                
                # Delete follow relationship using SQLAlchemy delete
                await db.execute(
                    delete(Follow).where(
                        and_(
                            Follow.followerId == follower_id,
                            Follow.followingId == following_id
                        )
                    )
                )
                await db.commit()
                
                return {"message": f"You have unfollowed {following_user.username}"}
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to unfollow user: {str(e)}")

    @staticmethod
    async def get_users_paginated(current_user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Calculate skip for pagination
                skip = (page - 1) * page_size
                
                # Get the IDs of users that the current user is following
                result = await db.execute(
                    select(Follow.followingId).where(Follow.followerId == current_user_id)
                )
                following_ids = [str(row[0]) for row in result.fetchall()]
                
                # Build where condition
                where_conditions = [User.id != current_user_id]
                if following_ids:
                    where_conditions.append(not_(User.id.in_(following_ids)))
                
                # Get users with pagination, excluding current user and users already followed
                result = await db.execute(
                    select(User)
                    .where(and_(*where_conditions))
                    .order_by(User.id.asc())
                    .offset(skip)
                    .limit(page_size)
                )
                users = result.scalars().all()
                
                # Manually exclude password
                users_without_password = [{
                    "id": str(user.id),
                    "username": user.username,
                    "fullName": user.fullName,
                    "email": user.email
                } for user in users]
                
                # Get total count for pagination info (excluding current user and followed users)
                count_result = await db.execute(
                    select(func.count(User.id)).where(and_(*where_conditions))
                )
                total_count = count_result.scalar() or 0
                
                return {
                    "users": users_without_password,
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 0
                }
                
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                raise ValueError(f"Failed to get users: {str(e)}")
    
    @staticmethod
    async def get_followers(user_id: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Find all follows where the current user is being followed
                result = await db.execute(
                    select(Follow.followerId).where(Follow.followingId == user_id)
                )
                follower_ids = [str(row[0]) for row in result.fetchall()]
                
                followers = []
                
                if follower_ids:
                    # Get the follower users
                    result = await db.execute(
                        select(User).where(User.id.in_(follower_ids))
                    )
                    users = result.scalars().all()
                    
                    followers = [{
                        "id": str(user.id),
                        "username": user.username,
                        "fullName": user.fullName,
                        "email": user.email
                    } for user in users]
                
                return {"followers": followers}
                
            except Exception as e:
                raise ValueError(f"Failed to get followers: {str(e)}")
    
    @staticmethod
    async def get_following(user_id: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Find all follows where the current user is following
                result = await db.execute(
                    select(Follow.followingId).where(Follow.followerId == user_id)
                )
                following_ids = [str(row[0]) for row in result.fetchall()]
                
                following = []
                
                if following_ids:
                    # Get the following users
                    result = await db.execute(
                        select(User).where(User.id.in_(following_ids))
                    )
                    users = result.scalars().all()
                    
                    following = [{
                        "id": str(user.id),
                        "username": user.username,
                        "fullName": user.fullName,
                        "email": user.email
                    } for user in users]
                
                return {"following": following}
                
            except Exception as e:
                raise ValueError(f"Failed to get following: {str(e)}")