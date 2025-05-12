from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from bson import ObjectId
from datetime import datetime

from app.core.security import get_current_active_user
from app.database.database import db, EMOTIONS_COLLECTION
from app.models.user import User, Emotion as UserEmotion
from app.services.user_service import UserService
from app.schemas.emotion import EmotionCreate, EmotionResponse

router = APIRouter(prefix="/emotions", tags=["Emotions"])
logger = logging.getLogger(__name__)

@router.get("/", status_code=status.HTTP_200_OK)
async def get_emotions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user's emotions
    """
    try:
        # Query MongoDB for emotions
        cursor = db[EMOTIONS_COLLECTION].find(
            {"userId": current_user.id}
        ).skip(skip).limit(limit).sort("recordedAt", -1)
        
        emotions = await cursor.to_list(length=limit)
        
        # Convert BSON to dict and format data
        emotion_list = []
        for emotion in emotions:
            emotion_list.append({
                "id": str(emotion["_id"]),
                "user_id": emotion["userId"],
                "emotion_type": emotion["emotionType"],
                "intensity": emotion["intensity"],
                "recorded_at": emotion["recordedAt"].isoformat() if isinstance(emotion["recordedAt"], datetime) else emotion["recordedAt"],
                "notes": emotion.get("notes", "")
            })
        
        # Get total count
        total_count = await db[EMOTIONS_COLLECTION].count_documents({"userId": current_user.id})
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Emotions retrieved successfully",
                "data": emotion_list,
                "meta": {
                    "skip": skip,
                    "limit": limit,
                    "total": total_count
                }
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving emotions: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error retrieving emotions: {str(e)}"
            }
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_emotion(
    emotion: EmotionCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Record a new emotion
    """
    try:
        # Validate intensity range
        if emotion.intensity < 1 or emotion.intensity > 10:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": 400,
                    "message": "Intensity must be between 1 and 10"
                }
            )
        
        # Create emotion document
        now = datetime.utcnow()
        emotion_doc = {
            "userId": current_user.id,
            "emotionType": emotion.emotion_type,
            "intensity": emotion.intensity,
            "notes": emotion.notes,
            "recordedAt": now
        }
        
        # Insert into database
        result = await db[EMOTIONS_COLLECTION].insert_one(emotion_doc)
        emotion_id = result.inserted_id
        
        # Also update the user's current emotion
        try:
            # Map emotion type string to Emotion enum
            emotion_enum = UserEmotion[emotion.emotion_type.upper()]
            await UserService.update_emotion(current_user.id, emotion_enum)
        except (KeyError, ValueError):
            logger.warning(f"Invalid emotion type: {emotion.emotion_type}")
            # Continue even if we can't update the user's emotion
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": 201,
                "message": "Emotion recorded successfully",
                "data": {
                    "id": str(emotion_id),
                    "user_id": current_user.id,
                    "emotion_type": emotion.emotion_type,
                    "intensity": emotion.intensity,
                    "recorded_at": now.isoformat(),
                    "notes": emotion.notes
                }
            }
        )
    except Exception as e:
        logger.error(f"Error creating emotion: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error creating emotion: {str(e)}"
            }
        )

@router.get("/{emotion_id}", status_code=status.HTTP_200_OK)
async def get_emotion(
    emotion_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific emotion record
    """
    try:
        # Query MongoDB for the emotion
        emotion = await db[EMOTIONS_COLLECTION].find_one({
            "_id": ObjectId(emotion_id),
            "userId": current_user.id
        })
        
        if emotion is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": 404,
                    "message": "Emotion not found"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Emotion retrieved successfully",
                "data": {
                    "id": str(emotion["_id"]),
                    "user_id": emotion["userId"],
                    "emotion_type": emotion["emotionType"],
                    "intensity": emotion["intensity"],
                    "recorded_at": emotion["recordedAt"].isoformat() if isinstance(emotion["recordedAt"], datetime) else emotion["recordedAt"],
                    "notes": emotion.get("notes", "")
                }
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving emotion: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error retrieving emotion: {str(e)}"
            }
        )

@router.delete("/{emotion_id}", status_code=status.HTTP_200_OK)
async def delete_emotion(
    emotion_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete an emotion record
    """
    try:
        # Delete the emotion from MongoDB
        result = await db[EMOTIONS_COLLECTION].delete_one({
            "_id": ObjectId(emotion_id),
            "userId": current_user.id
        })
        
        if result.deleted_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": 404,
                    "message": "Emotion not found"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": 200,
                "message": "Emotion deleted successfully"
            }
        )
    except Exception as e:
        logger.error(f"Error deleting emotion: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": f"Error deleting emotion: {str(e)}"
            }
        ) 