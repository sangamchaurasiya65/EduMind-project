from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ChapterProgressItem(BaseModel):
    id: int
    title: str
    status: str  # 'completed', 'current', 'locked', 'not_started'
    duration: str

    model_config = ConfigDict(from_attributes=True)


class SubjectProgressResponse(BaseModel):
    id: str
    name: str
    code: str
    description: str
    color: str
    bg: str
    status: str  # 'Not Started', 'In Progress', 'Completed'
    status_key: str  # 'not-started', 'in-progress', 'completed'
    progress_percent: int
    current_topic: str
    materials_count: int
    study_sessions_count: int
    quiz_attempts_count: int
    topics_completed: int
    total_topics: int
    last_activity_at: Optional[str] = None
    chapters: List[ChapterProgressItem] = []

    model_config = ConfigDict(from_attributes=True)
