from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.user import Emotion


class EmotionBase(BaseModel):
    emotion_type: Emotion
    intensity: int = Field(ge=1, le=10, default=5)
    notes: Optional[str] = None


class EmotionCreate(EmotionBase):
    pass


class EmotionUpdate(BaseModel):
    emotion_type: Optional[Emotion] = None
    intensity: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class EmotionResponse(EmotionBase):
    id: str
    user_id: str
    recorded_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class EmotionsListResponse(BaseModel):
    items: List[EmotionResponse]
    total: int 