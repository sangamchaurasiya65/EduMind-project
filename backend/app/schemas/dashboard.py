from typing import List, Optional, Union
from pydantic import BaseModel


class ContinueLearningItem(BaseModel):
    id: Union[int, str]
    name: str
    code: str
    progress: int
    currentTopic: str
    accentColor: str
    bgLight: str


class WeeklyBarData(BaseModel):
    day: str
    hours: float
    height: str
    isHighest: bool = False


class RecentActivityItem(BaseModel):
    id: Union[int, str]
    title: str
    time: str
    iconBg: str
    iconColor: str
    badge: str


class DashboardStatsResponse(BaseModel):
    study_hours: str
    total_study_seconds: int
    active_subjects_count: int
    quiz_attempts_count: int
    competency_score: str
    competency_subtitle: str
    weekly_hours_total: str
    weekly_data: List[WeeklyBarData]
    continue_learning: List[ContinueLearningItem]
    recent_activities: List[RecentActivityItem]
