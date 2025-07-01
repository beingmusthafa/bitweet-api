from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import ValidationError
from schemas.auth_schemas import UserRegistrationRequest, UserRegistrationResponse
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