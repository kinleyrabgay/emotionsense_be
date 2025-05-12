from datetime import datetime
from typing import Dict, Any, Optional
from app.models.user import Emotion as EmotionEnum

class Emotion:
    def __init__(
        self,
        user_id: str,
        emotion_type: EmotionEnum,
        intensity: int = 5,
        notes: str = None,
        recorded_at: datetime = None,
        id: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.emotion_type = emotion_type
        self.intensity = intensity
        self.notes = notes
        self.recorded_at = recorded_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert emotion to dictionary for MongoDB storage"""
        return {
            "userId": self.user_id,
            "emotionType": self.emotion_type.value if isinstance(self.emotion_type, EmotionEnum) else self.emotion_type,
            "intensity": self.intensity,
            "notes": self.notes,
            "recordedAt": self.recorded_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create Emotion object from MongoDB document"""
        if not data:
            return None
            
        # Handle _id from MongoDB
        id_value = str(data.get("_id")) if data.get("_id") else None
        
        # Convert emotion type value to Enum
        emotion_value = data.get("emotionType", EmotionEnum.NEUTRAL.value)
        if isinstance(emotion_value, int) or (isinstance(emotion_value, str) and emotion_value.isdigit()):
            emotion_type = EmotionEnum(int(emotion_value))
        else:
            # Default to NEUTRAL if invalid
            emotion_type = EmotionEnum.NEUTRAL
            
        return cls(
            id=id_value,
            user_id=data.get("userId", ""),
            emotion_type=emotion_type,
            intensity=data.get("intensity", 5),
            notes=data.get("notes"),
            recorded_at=data.get("recordedAt", datetime.utcnow())
        ) 