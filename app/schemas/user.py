from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class Emotion(int, Enum):
    HAPPY = 0
    SAD = 1
    ANGRY = 2
    SURPRISED = 3
    NEUTRAL = 4


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class EmotionHistoryEntry(BaseModel):
    timestamp: datetime
    emotion: Emotion


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str
    profile: Optional[str] = ""
    is_face_auth_enabled: Optional[bool] = False
    role: Optional[UserRole] = UserRole.EMPLOYEE
    
    class Config:
        # Allow population by field name
        populate_by_name = True
        # Make API more flexible for client side variations
        extra = "ignore"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile: Optional[str] = None
    role: Optional[UserRole] = None
    
    class Config:
        populate_by_name = True
        extra = "ignore"


class EmotionUpdate(BaseModel):
    emotion: Emotion


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    profile: Optional[str] = None
    current_emotion: Optional[Emotion] = Emotion.NEUTRAL
    role: UserRole = UserRole.EMPLOYEE
    is_face_auth_enabled: bool = False
    emotion_history: Optional[List[EmotionHistoryEntry]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse 