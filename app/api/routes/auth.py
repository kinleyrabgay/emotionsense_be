from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
import re
import logging

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_active_user
)
from app.database.database import db, USERS_COLLECTION
from app.models.user import User, Emotion as UserEmotion
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse, UserLogin, Emotion
from app.services.user_service import UserService

# Create router without the prefix - we'll add the prefix in main.py
router = APIRouter(tags=["Authentication"])
logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email format using regex"""
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    
    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter"
    
    return True, ""


def get_emotion_data(user: User):
    """Get emotion data in a consistent format"""
    emotion_value = user.current_emotion
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile": user.profile,
        "emotion": emotion_value.name if isinstance(emotion_value, UserEmotion) else None,
        "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else user.created_at,
        "updated_at": user.updated_at.isoformat() if isinstance(user.updated_at, datetime) else user.updated_at,
        "emotion_history": [
            {
                "emotion": entry.emotion.name if isinstance(entry.emotion, UserEmotion) else None,
                "timestamp": entry.timestamp.isoformat() if isinstance(entry.timestamp, datetime) else entry.timestamp
            } 
            for entry in user.emotion_history
        ] if user.emotion_history else []
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    try:
        # Check if user already exists
        existing_user = await UserService.find_by_email(user.email)
        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": 400, "message": "Email already registered"}
            )
        
        # Validate email format
        if not validate_email(user.email):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": 400, "message": "Invalid email format"}
            )
        
        # Validate password strength
        is_valid_password, password_error = validate_password(user.password)
        if not is_valid_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": 400, "message": password_error}
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        new_user = User(
            email=user.email,
            name=user.name,
            password=hashed_password,
            profile="",
            current_emotion=UserEmotion.NEUTRAL
        )
        
        # Save to database
        created_user = await UserService.create_user(new_user)
        if not created_user:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": 500, "message": "Failed to create user"}
            )
        
        # Return success response
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": 201,
                "message": "User registered successfully",
                "data": get_emotion_data(created_user)
            }
        )
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": 500, "message": f"Error during registration: {str(e)}"}
        )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_data: UserLogin):
    """Login endpoint that accepts JSON data"""
    try:
        # Find user by email
        user = await UserService.find_by_email(user_data.email)
        if not user or not verify_password(user_data.password, user.password):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": 401,
                    "message": "Incorrect email or password"
                }
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Create response with token and user data
        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Login successful",
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": get_emotion_data(user)
                }
            }
        )
        
        # Set auth cookie (optional, for web browsers)
        expires = datetime.utcnow() + access_token_expires
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            expires=expires.timestamp(),
            path="/",
            domain=None,
            secure=False,  # Set to True in production with HTTPS
            httponly=True,
            samesite="lax"
        )
        
        return response
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error during login: {str(e)}"
            }
        )


@router.post("/token", status_code=status.HTTP_200_OK)
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Standard OAuth2 compatible login endpoint that takes form data - used by Swagger UI"""
    try:
        # Find user by email
        user = await UserService.find_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # This response format is required for OAuth2 compatibility
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during token generation: {str(e)}"
        )


@router.get("/user/me", status_code=status.HTTP_200_OK)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile (alternative endpoint path for client compatibility)
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": 200,
            "message": "User profile retrieved successfully",
            "data": get_emotion_data(current_user)
        }
    )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile from auth token
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "User profile retrieved successfully",
                "data": get_emotion_data(current_user)
            }
        )
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error getting current user: {str(e)}"
            }
        )


@router.options("/logout")
async def logout_options():
    """
    Handle OPTIONS request for the logout endpoint (for CORS preflight)
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={}
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    Handle user logout
    
    Note: Since we're using JWT tokens, the server doesn't actually invalidate
    the token (JWT is stateless). The client should clear their token storage.
    This endpoint provides a consistent API for clients.
    """
    # Create response
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": 200,
            "message": "Logout successful"
        }
    )
    
    # Clear auth cookie if present
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=None,
        secure=False,  # Set to True in production with HTTPS
        httponly=True
    )
    
    return response 