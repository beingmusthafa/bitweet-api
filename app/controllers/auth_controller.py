from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import ValidationError
from schemas.auth_schemas import UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRegistrationResponse)
async def register_user(request: Request, response: Response):
    try:
        body = await request.json()
        user_data = UserRegistrationRequest(**body)
        
        # Call service layer
        user_response, tokens = await AuthService.register_user(user_data)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return user_response
        
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

@router.post("/login", response_model=UserLoginResponse)
async def login_user(request: Request, response: Response):
    try:
        body = await request.json()
        user_data = UserLoginRequest(**body)
        
        # Call service layer
        user_response, tokens = await AuthService.login_user(user_data)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return user_response
        
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

@router.post("/logout")
async def logout_user(request: Request, response: Response):
    try:
        # Get refresh token from cookies
        refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Blacklist the refresh token
            await AuthService.logout_user(refresh_token)
        
        # Clear cookies
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        # Still clear cookies even if blacklisting fails
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        raise HTTPException(status_code=500, detail="Internal server error")