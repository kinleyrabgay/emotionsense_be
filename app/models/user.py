from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

class Emotion(int, Enum):
    HAPPY = 0
    SAD = 1
    ANGRY = 2
    SURPRISED = 3
    NEUTRAL = 4

class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class EmotionHistoryEntry:
    def __init__(self, timestamp: datetime, emotion: Emotion):
        self.timestamp = timestamp
        self.emotion = emotion
        
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "emotion": self.emotion.value if isinstance(self.emotion, Emotion) else self.emotion
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            timestamp=data.get("timestamp", datetime.utcnow()),
            emotion=Emotion(data.get("emotion", Emotion.NEUTRAL.value))
        )

class User:
    def __init__(
        self,
        name: str,
        email: str,
        password: str,
        profile: str = "",
        current_emotion: Emotion = Emotion.NEUTRAL,
        role: UserRole = UserRole.EMPLOYEE,
        emotion_history: List[EmotionHistoryEntry] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        id: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password  # This should be hashed
        self.profile = profile
        self.current_emotion = current_emotion
        self.role = role
        self.emotion_history = emotion_history or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for MongoDB storage"""
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "profile": self.profile,
            "currentEmotion": self.current_emotion.value if isinstance(self.current_emotion, Emotion) else self.current_emotion,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "emotionHistory": [entry.to_dict() for entry in self.emotion_history],
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create User object from MongoDB document"""
        if not data:
            return None
            
        # Handle _id from MongoDB
        id_value = str(data.get("_id")) if data.get("_id") else None
        
        # Convert emotion value to Enum
        emotion_value = data.get("currentEmotion", Emotion.NEUTRAL.value)
        if isinstance(emotion_value, int) or (isinstance(emotion_value, str) and emotion_value.isdigit()):
            emotion = Emotion(int(emotion_value))
        else:
            # Default to NEUTRAL if invalid
            emotion = Emotion.NEUTRAL
            
        # Convert role string to Enum
        role_value = data.get("role", UserRole.EMPLOYEE.value)
        try:
            role = UserRole(role_value)
        except ValueError:
            # Default to EMPLOYEE if invalid
            role = UserRole.EMPLOYEE
            
        # Convert emotion history entries
        emotion_history = []
        for entry in data.get("emotionHistory", []):
            emotion_history.append(EmotionHistoryEntry.from_dict(entry))
            
        return cls(
            id=id_value,
            name=data.get("name", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            profile=data.get("profile", ""),
            current_emotion=emotion,
            role=role,
            emotion_history=emotion_history,
            created_at=data.get("createdAt", datetime.utcnow()),
            updated_at=data.get("updatedAt", datetime.utcnow())
        )
        
    def add_emotion_history(self, emotion: Emotion):
        """Add a new entry to the emotion history"""
        entry = EmotionHistoryEntry(datetime.utcnow(), emotion)
        self.emotion_history.append(entry)
        self.current_emotion = emotion
        self.updated_at = datetime.utcnow()
        return entry 