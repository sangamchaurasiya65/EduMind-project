from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TopicProgressItem(BaseModel):
    id: int
    title: str
    summary: Optional[str] = ""
    estimated_minutes: int = 15
    status: str  # 'not_started', 'reading', 'practised', 'mastered'
    status_label: str  # 'Not started', 'Reading', 'Practised', 'Mastered'
    credit_percent: int  # 0, 25, 50, 100
    quiz_attempts_count: int = 0
    best_score: Optional[float] = None
    has_read: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChapterProgressItem(BaseModel):
    id: int
    title: str
    status: str  # 'completed', 'current', 'not_started'
    duration: str
    material_id: Optional[int] = None
    topics_count: int = 0
    topics_mastered: int = 0
    topics: List[TopicProgressItem] = []

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
