from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from bson import ObjectId

from app.core.security import get_current_active_user
from app.database.database import db, USERS_COLLECTION
from app.models.user import User, Emotion as UserEmotion
from app.schemas.user import UserResponse, EmotionUpdate, Emotion
from app.utils.websocket_manager import manager
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger(__name__)


@router.get("/me", status_code=status.HTTP_200_OK)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile
    """
    try:
        emotion_value = current_user.current_emotion
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "User profile retrieved successfully",
                "data": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "profile": current_user.profile,
                    "emotion": emotion_value.name if isinstance(emotion_value, UserEmotion) else None,
                    "created_at": current_user.created_at.isoformat() if hasattr(current_user, 'created_at') and current_user.created_at else None,
                    "updated_at": current_user.updated_at.isoformat() if hasattr(current_user, 'updated_at') and current_user.updated_at else None,
                    "emotion_history": [
                        {
                            "emotion": entry.emotion.name if isinstance(entry.emotion, UserEmotion) else None,
                            "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') and entry.timestamp else None
                        } 
                        for entry in current_user.emotion_history
                    ] if current_user.emotion_history else []
                }
            }
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error getting user profile: {str(e)}"
            }
        )


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user by ID (admin only)
    """
    try:
        if user_id != current_user.id:
            # In a real app, you might check if the current user is an admin
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": 403,
                    "message": "Not authorized to access this user"
                }
            )
        
        # Find user by ID
        user = await UserService.find_by_id(user_id)
        if user is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": 404,
                    "message": "User not found"
                }
            )
        
        emotion_value = user.current_emotion
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "User profile retrieved successfully",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "profile": user.profile,
                    "emotion": emotion_value.name if isinstance(emotion_value, UserEmotion) else None,
                    "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
                    "emotion_history": [
                        {
                            "emotion": entry.emotion.name if isinstance(entry.emotion, UserEmotion) else None,
                            "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') and entry.timestamp else None
                        } 
                        for entry in user.emotion_history
                    ] if user.emotion_history else []
                }
            }
        )
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error getting user by ID: {str(e)}"
            }
        )


@router.patch("/me/emotion", status_code=status.HTTP_200_OK)
async def update_current_emotion(
    emotion_data: EmotionUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update the current user's emotional state
    """
    try:
        # Update the current user's emotion
        emotion_enum = emotion_data.emotion
        success = await UserService.update_emotion(current_user.id, emotion_enum.value)
        
        if not success:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": 500,
                    "message": "Failed to update emotion"
                }
            )
        
        # Broadcast the emotion update via WebSocket
        emotion_data_dict = {
            "name": emotion_enum.name,
            "value": emotion_enum.value,
            "timestamp": None  # We'll use the server timestamp
        }
        await manager.broadcast_emotion_update(current_user.id, emotion_data_dict)
        
        # Get updated user
        updated_user = await UserService.find_by_id(current_user.id)
        if not updated_user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": 404, 
                    "message": "User not found after update"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Current emotion updated successfully",
                "data": {
                    "id": updated_user.id,
                    "name": updated_user.name,
                    "email": updated_user.email,
                    "profile": updated_user.profile,
                    "emotion": emotion_enum.name,
                    "created_at": updated_user.created_at.isoformat() if hasattr(updated_user, 'created_at') and updated_user.created_at else None,
                    "updated_at": updated_user.updated_at.isoformat() if hasattr(updated_user, 'updated_at') and updated_user.updated_at else None,
                }
            }
        )
    except Exception as e:
        logger.error(f"Error updating emotion: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error updating emotion: {str(e)}"
            }
        ) 