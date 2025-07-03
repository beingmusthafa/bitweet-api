from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import ValidationError
from schemas.user_schemas import SendOTPRequest, ChangePasswordRequest
from services.user_service import UserService
from utils.auth_middleware import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/password/send-otp")
async def send_password_reset_otp(request: Request, current_user=Depends(get_current_user)):
    try:
        # Call service layer to generate and send OTP
        result = await UserService.generate_and_send_otp(current_user["id"])
        
        return {"message": "OTP sent successfully"}
        
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

@router.put("/password/change")
async def change_password(request: Request, current_user=Depends(get_current_user)):
    try:
        body = await request.json()
        change_request = ChangePasswordRequest(**body)
        
        # Call service layer to verify OTP and change password
        result = await UserService.verify_otp_and_change_password(
            user_id=current_user["id"],
            otp=change_request.otp,
            new_password=change_request.password
        )
        
        return {"message": "Password changed successfully"}
        
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field_name = error['loc'][-1] if error['loc'] else 'unknown'
            errors[field_name] = error['msg']
        raise HTTPException(status_code=400, detail={"errors": errors})
    except ValueError as e:
        error_message = str(e)
        # Return specific error messages with 400 status code
        if "New password cannot be the same as your current password" in error_message:
            raise HTTPException(status_code=400, detail={"message": error_message})
        elif "Invalid or expired OTP" in error_message:
            raise HTTPException(status_code=400, detail={"message": error_message})
        elif any(msg in error_message for msg in ["at least 8 characters", "uppercase letter", "number", "special character"]):
            raise HTTPException(status_code=400, detail={"message": error_message})
        else:
            raise HTTPException(status_code=400, detail={"message": error_message})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})