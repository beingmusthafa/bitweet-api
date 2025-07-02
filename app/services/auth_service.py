from passlib.context import CryptContext
from prisma.errors import UniqueViolationError
from database.connection import get_db
from schemas.auth_schemas import UserRegistrationRequest, UserLoginRequest
from utils.token_utils import generate_tokens
from typing import Dict, Tuple

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
        db = await get_db()
        
        try:
            # Hash password
            hashed_password = AuthService.hash_password(user_data.password)
            
            # Create user
            user = await db.user.create(
                data={
                    "email": user_data.email,
                    "username": user_data.username,
                    "fullName": user_data.fullName,
                    "password": hashed_password
                }
            )
            
            # Generate tokens
            tokens = generate_tokens(user.id)
            
            # Return user data (without password) and tokens
            user_response = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "fullName": user.fullName,
                "message": "User registered successfully"
            }
            
            return user_response, tokens
            
        except UniqueViolationError as e:
            error_msg = str(e)
            if "email" in error_msg:
                raise ValueError("Email already exists")
            elif "username" in error_msg:
                raise ValueError("Username already exists")
            else:
                raise ValueError("User already exists")
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")
    
    @staticmethod
    async def login_user(user_data: UserLoginRequest) -> Tuple[Dict, Dict[str, str]]:
        db = await get_db()
        
        try:
            # Find user by email or username
            user = await db.user.find_first(
                where={
                    "OR": [
                        {"email": user_data.identifier},
                        {"username": user_data.identifier}
                    ]
                }
            )
            
            if not user or not AuthService.verify_password(user_data.password, user.password):
                raise ValueError("Invalid credentials")
            
            # Generate tokens
            tokens = generate_tokens(user.id)
            
            # Return user data (without password) and tokens
            user_response = {
                "id": user.id,
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
        db = await get_db()
        
        try:
            # Blacklist the refresh token
            await db.blacklistedtoken.create(
                data={"token": refresh_token}
            )
            
            return {"message": "Logout successful"}
            
        except Exception as e:
            raise ValueError(f"Logout failed: {str(e)}")
    