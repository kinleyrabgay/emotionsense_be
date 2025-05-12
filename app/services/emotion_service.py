from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging

from app.database.database import db, EMOTIONS_COLLECTION
from app.models.emotion import Emotion

logger = logging.getLogger(__name__)

class EmotionService:
    @staticmethod
    async def find_by_id(emotion_id: str) -> Optional[Emotion]:
        """Find an emotion by ID"""
        try:
            emotion_data = await db[EMOTIONS_COLLECTION].find_one({"_id": ObjectId(emotion_id)})
            return Emotion.from_dict(emotion_data) if emotion_data else None
        except Exception as e:
            logger.error(f"Error finding emotion by ID: {str(e)}")
            return None
            
    @staticmethod
    async def find_by_user_id(user_id: str, limit: int = 100) -> List[Emotion]:
        """Find emotions for a user"""
        try:
            cursor = db[EMOTIONS_COLLECTION].find({"userId": user_id}).sort("recordedAt", -1).limit(limit)
            emotions_data = await cursor.to_list(length=limit)
            return [Emotion.from_dict(data) for data in emotions_data if data]
        except Exception as e:
            logger.error(f"Error finding emotions by user ID: {str(e)}")
            return []
            
    @staticmethod
    async def create_emotion(emotion: Emotion) -> Optional[Emotion]:
        """Create a new emotion entry"""
        try:
            emotion_dict = emotion.to_dict()
            result = await db[EMOTIONS_COLLECTION].insert_one(emotion_dict)
            if result.inserted_id:
                emotion.id = str(result.inserted_id)
                return emotion
            return None
        except Exception as e:
            logger.error(f"Error creating emotion: {str(e)}")
            return None
            
    @staticmethod
    async def update_emotion(emotion_id: str, update_data: Dict[str, Any]) -> bool:
        """Update emotion data"""
        try:
            # Convert field names to camelCase for MongoDB
            mongo_update = {}
            field_mapping = {
                "emotion_type": "emotionType",
                "intensity": "intensity",
                "notes": "notes",
                "recorded_at": "recordedAt"
            }
            
            for key, value in update_data.items():
                if key in field_mapping:
                    mongo_update[field_mapping[key]] = value
            
            if not mongo_update:
                return False
                
            result = await db[EMOTIONS_COLLECTION].update_one(
                {"_id": ObjectId(emotion_id)},
                {"$set": mongo_update}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating emotion: {str(e)}")
            return False
            
    @staticmethod
    async def delete_emotion(emotion_id: str) -> bool:
        """Delete an emotion entry"""
        try:
            result = await db[EMOTIONS_COLLECTION].delete_one({"_id": ObjectId(emotion_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting emotion: {str(e)}")
            return False 