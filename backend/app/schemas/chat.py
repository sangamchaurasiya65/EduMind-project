from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ChatMessageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    subject_code: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Student's study query or prompt")
    subject_code: Optional[str] = Field(None, description="Current study subject code from context")
    subject_name: Optional[str] = Field(None, description="Current study subject title from context")
    topic: Optional[str] = Field(None, description="Current study topic from context")
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Prior conversation turns for multi-turn dialogue (max 15 messages)"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Message cannot be empty.")
        if len(clean) > 4000:
            raise ValueError("Message exceeds maximum allowed length of 4000 characters.")
        return clean


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageItem]


class ClearChatResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int

