from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class StudySessionStartRequest(BaseModel):
    subject_id: Optional[str] = Field(None, description="Associated subject ID or code")


class StudySessionHeartbeatRequest(BaseModel):
    delta_seconds: Optional[int] = Field(30, ge=1, le=120, description="Active study duration delta in seconds")


class StudySessionResponse(BaseModel):
    id: int
    user_id: str
    subject_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int

    model_config = ConfigDict(from_attributes=True)

