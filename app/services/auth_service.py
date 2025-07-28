from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from database.connection import AsyncSessionLocal
from database.models import User, BlacklistedToken
from schemas.auth_schemas import UserRegistrationRequest, UserLoginRequest
from utils.token_utils import generate_tokens
from utils.security_middleware import sanitize_string
from typing import Dict, Tuple
from sqlalchemy import select, or_

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def register_user(user_data: UserRegistrationRequest) -> Tuple[Dict, Dict[str, str]]:
        async with AsyncSessionLocal() as db:
            try:
                # Hash password
                hashed_password = AuthService.hash_password(user_data.password)
                
                # Sanitize user input fields
                sanitized_email = sanitize_string(user_data.email)
                sanitized_username = sanitize_string(user_data.username)
                sanitized_fullname = sanitize_string(user_data.fullName)
                
                # Create user
                user = User(
                    email=sanitized_email,
                    username=sanitized_username,
                    fullName=sanitized_fullname,
                    password=hashed_password
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                # Generate tokens
                tokens = generate_tokens(str(user.id))
                
                # Return user data (without password) and tokens
                user_response = {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "fullName": user.fullName,
                    "message": "User registered successfully"
                }
                
                return user_response, tokens
                
            except IntegrityError as e:
                await db.rollback()
                error_msg = str(e)
                if "email" in error_msg:
                    raise ValueError("Email already exists")
                elif "username" in error_msg:
                    raise ValueError("Username already exists")
                else:
                    raise ValueError("User already exists")
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Registration failed: {str(e)}")
    
    @staticmethod
    async def login_user(user_data: UserLoginRequest) -> Tuple[Dict, Dict[str, str]]:
        async with AsyncSessionLocal() as db:
            try:
                # Find user by email or username
                result = await db.execute(
                    select(User).where(
                        or_(
                            User.email == user_data.identifier,
                            User.username == user_data.identifier
                        )
                    )
                )
                user = result.scalar_one_or_none()
                
                if not user or not AuthService.verify_password(user_data.password, str(user.password)):
                    raise ValueError("Invalid credentials")
                
                # Generate tokens
                tokens = generate_tokens(str(user.id))
                
                # Return user data (without password) and tokens
                user_response = {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "fullName": user.fullName,
                    "message": "Login successful"
                }
                
                return user_response, tokens
                
            except Exception as e:
                if "Invalid credentials" in str(e):
                    raise ValueError("Invalid credentials")
                raise ValueError(f"Login failed: {str(e)}")
    
    @staticmethod
    async def logout_user(refresh_token: str) -> Dict:
        async with AsyncSessionLocal() as db:
            try:
                # Blacklist the refresh token
                blacklisted_token = BlacklistedToken(token=refresh_token)
                db.add(blacklisted_token)
                await db.commit()
                
                return {"message": "Logout successful"}
                
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Logout failed: {str(e)}")
    