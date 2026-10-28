from typing import Optional, Dict, Any, List
import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the learner")
    email: str = Field(..., description="College or institutional email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")
    course: Optional[str] = Field(None, description="Degree or course program (e.g. B.Tech CSE)")
    semester: Optional[str] = Field(None, description="Academic semester (e.g. 6th Semester)")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full name must contain at least 2 characters.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format. Please provide a valid email address.")
        return clean

    @model_validator(mode="after")
    def verify_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirmation password do not match.")
        return self


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    course: Optional[str] = None
    semester: Optional[str] = None
    role: Optional[str] = "Student"
    learning_style: Optional[str] = None
    daily_goal: Optional[str] = None
    preferred_subject: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    role: Optional[str] = None


class PreferencesUpdateRequest(BaseModel):
    learning_style: Optional[str] = None
    daily_goal: Optional[str] = None
    preferred_subject: Optional[str] = None


class ActivityLogRequest(BaseModel):
    activity_type: str = Field(..., description="Type of study activity performed")
    details: Optional[str] = None


class TopicToggleRequest(BaseModel):
    topic_title: str = Field(..., description="Title of the topic/chapter to toggle")
    completed: Optional[bool] = Field(None, description="Force completed status, or toggle if omitted")

