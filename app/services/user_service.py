from typing import List, Optional, Dict, Any

import logging

from bson import ObjectId

from app.database.database import db, USERS_COLLECTION
from app.models.user import User, Emotion

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def find_by_email(email: str) -> Optional[User]:
        """Find a user by email"""
        user_data = await db[USERS_COLLECTION].find_one({"email": email})
        return User.from_dict(user_data) if user_data else None
        
    @staticmethod
    async def find_by_id(user_id: str) -> Optional[User]:
        """Find a user by ID"""
        try:
            user_data = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
            
    @staticmethod
    async def create_user(user: User) -> Optional[User]:
        """Create a new user"""
        try:
            user_dict = user.to_dict()
            result = await db[USERS_COLLECTION].insert_one(user_dict)
            if result.inserted_id:
                user.id = str(result.inserted_id)
                return user
            return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
            
    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            # Convert field names to camelCase for MongoDB
            mongo_update = {}
            field_mapping = {
                "name": "name",
                "email": "email",
                "password": "password",
                "profile": "profile",
                "current_emotion": "currentEmotion",
                "role": "role",
                "emotion_history": "emotionHistory"
            }
            
            for key, value in update_data.items():
                if key in field_mapping:
                    mongo_update[field_mapping[key]] = value
            
            if not mongo_update:
                return False
                
            result = await db[USERS_COLLECTION].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": mongo_update}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
            
    @staticmethod
    async def update_emotion(user_id: str, emotion: Emotion) -> bool:
        """Update user's current emotion and add to history"""
        try:
            # Get the user
            user_data = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
            if not user_data:
                return False
                
            user = User.from_dict(user_data)
            
            # Create new emotion history entry
            entry = user.add_emotion_history(emotion)
            
            # Update the user
            result = await db[USERS_COLLECTION].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "currentEmotion": emotion.value if isinstance(emotion, Emotion) else emotion,
                        "updatedAt": user.updated_at
                    },
                    "$push": {
                        "emotionHistory": entry.to_dict()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user emotion: {str(e)}")
            return False 