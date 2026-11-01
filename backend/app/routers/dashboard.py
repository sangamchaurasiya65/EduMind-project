from datetime import datetime, timezone, timedelta
from typing import List, Set, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.material import LearningMaterial
from backend.app.models.quiz import Quiz, QuizQuestion
from backend.app.models.attempt import QuizAttempt
from backend.app.models.study_session import StudySession
from backend.app.models.user import User
from backend.app.schemas.dashboard import (
    DashboardStatsResponse,
    ContinueLearningItem,
    WeeklyBarData,
    RecentActivityItem
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.competency_analyzer import calculate_competencies
from backend.app.services.subject_progress_service import (
    get_active_subjects_for_user,
    compute_user_subject_progress,
    matches_subject
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Real Statistics"])


def format_relative_time(dt: Optional[datetime], now_utc: datetime) -> str:
    if not dt:
        return "Recently"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now_utc - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 60:
        return "Just now"
    if total_seconds < 3600:
        mins = total_seconds // 60
        return f"{mins}m ago"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return "Today" if dt.date() == now_utc.date() else f"{hours}h ago"
    if total_seconds < 172800:
        return "Yesterday"
    days = total_seconds // 86400
    return f"{days} days ago"


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Retrieve live database-driven stats for the authenticated student"
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DashboardStatsResponse:
    """
    Computes all dashboard metrics strictly from REAL user activity in SQLite:
    - Study Hours: SUM(duration_seconds) formatted with 1 decimal (0.0 hrs if no sessions).
    - Subjects: Real count of active subjects created/enrolled by this user.
    - Quizzes: Real count of submitted quiz attempts by this user.
    - Competency Score: Verified quiz accuracy percentage or '0%' with 'No data yet'.
    - Continue Learning: Real enrolled subjects with live progress (0% / Not started yet if new).
    - Weekly Chart: Actual study hours per day for current week (0% if none).
    - Recent Activity: Live timeline of completed quizzes, uploaded notes, and study sessions.
    """
    now_utc = datetime.now(timezone.utc)
    user_id_str = str(current_user.id)

    # 1. Strict User Filter Conditions (Guarantees multi-tenant isolation)
    session_filter = (StudySession.user_id == user_id_str)
    material_filter = (LearningMaterial.user_id == user_id_str)
    attempt_filter = (QuizAttempt.user_id == user_id_str)

    # 2. Total Study Hours & Seconds
    total_study_seconds = db.query(
        func.coalesce(func.sum(StudySession.duration_seconds), 0)
    ).filter(session_filter).scalar() or 0

    study_hours_float = total_study_seconds / 3600.0
    study_hours_formatted = f"{study_hours_float:.1f}"

    # 3. Active Subjects Identification
    active_subjects = get_active_subjects_for_user(db, user_id=user_id_str)
    active_subjects_count = len(active_subjects)

    # 4. Completed Quiz Attempts Count
    completed_attempts_count = db.query(QuizAttempt).filter(
        attempt_filter,
        QuizAttempt.status == "completed"
    ).count()

    # 5. Competency Score Calculation
    competency_data = calculate_competencies(db, user_id=user_id_str)
    if competency_data.has_data and competency_data.total_questions_evaluated > 0:
        competency_score = f"{round(competency_data.overall_accuracy_percentage)}%"
        competency_subtitle = "Verified Accuracy"
    else:
        competency_score = "0%"
        competency_subtitle = "No data yet"

    # 6. Continue Learning Subjects List
    # Strictly populated from user's active subjects
    continue_learning: List[ContinueLearningItem] = []
    for subj_def in active_subjects:
        progress_info = compute_user_subject_progress(db, user_id=user_id_str, subject_def=subj_def)
        continue_learning.append(
            ContinueLearningItem(
                id=subj_def["id"],
                name=subj_def["name"],
                code=subj_def["code"],
                progress=progress_info["progress_percent"],
                currentTopic=progress_info["current_topic"],
                accentColor=subj_def.get("color", "#4f46e5"),
                bgLight=subj_def.get("bg", "#eef2ff")
            )
        )

    # 7. Weekly Study Activity (Monday to Sunday for current week)
    sessions = db.query(StudySession).filter(session_filter).all()
    weekday_index = now_utc.weekday()  # Monday is 0, Sunday is 6
    start_of_week = (now_utc - timedelta(days=weekday_index)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_raw_data = []

    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        day_seconds = sum(
            s.duration_seconds for s in sessions
            if s.started_at and day_start <= (s.started_at if s.started_at.tzinfo else s.started_at.replace(tzinfo=timezone.utc)) < day_end
        )
        day_hours = round(day_seconds / 3600.0, 1)
        weekly_raw_data.append({
            "day": day_labels[i],
            "hours": day_hours
        })

    max_day_hours = max((d["hours"] for d in weekly_raw_data), default=0)
    weekly_data: List[WeeklyBarData] = []

    for d in weekly_raw_data:
        if max_day_hours > 0 and d["hours"] > 0:
            height = f"{max(15, int((d['hours'] / max_day_hours) * 100))}%"
            is_highest = (d["hours"] == max_day_hours)
        else:
            height = "0%"
            is_highest = False

        weekly_data.append(
            WeeklyBarData(
                day=d["day"],
                hours=d["hours"],
                height=height,
                isHighest=is_highest
            )
        )

    weekly_total_sum = round(sum(d["hours"] for d in weekly_raw_data), 1)
    weekly_hours_total = f"{weekly_total_sum:.1f} hrs total"

    # 8. Real Recent Activities
    raw_activities = []
    attempts = db.query(QuizAttempt).filter(attempt_filter).all()
    materials = db.query(LearningMaterial).filter(material_filter).all()

    # Completed Quizzes
    for att in sorted(attempts, key=lambda a: a.completed_at or a.started_at, reverse=True)[:5]:
        if att.status == "completed":
            att_time = att.completed_at or att.started_at
            raw_activities.append({
                "timestamp": att_time,
                "title": f'Completed "{att.quiz.title if att.quiz else "Quiz"}" assessment',
                "time": format_relative_time(att_time, now_utc),
                "iconBg": "#ecfdf5",
                "iconColor": "#10b981",
                "badge": f"Score {int(att.score_percentage)}%"
            })

    # Uploaded Materials
    for m in sorted(materials, key=lambda mat: mat.created_at, reverse=True)[:5]:
        raw_activities.append({
            "timestamp": m.created_at,
            "title": f'Uploaded {m.title}',
            "time": format_relative_time(m.created_at, now_utc),
            "iconBg": "#f0f9ff",
            "iconColor": "#0ea5e9",
            "badge": "Material Ready"
        })

    # Study Sessions with duration >= 60s
    for s in sorted([sess for sess in sessions if sess.duration_seconds >= 60], key=lambda x: x.started_at, reverse=True)[:5]:
        raw_activities.append({
            "timestamp": s.started_at,
            "title": f'Studied {s.subject_id or "Subject"}',
            "time": format_relative_time(s.started_at, now_utc),
            "iconBg": "#f5f3ff",
            "iconColor": "#7c3aed",
            "badge": f"{max(1, s.duration_seconds // 60)} min session"
        })

    # Sort all by timestamp descending, take top 4
    raw_activities.sort(
        key=lambda act: act["timestamp"].replace(tzinfo=timezone.utc) if act["timestamp"].tzinfo is None else act["timestamp"],
        reverse=True
    )

    recent_activities: List[RecentActivityItem] = [
        RecentActivityItem(
            id=i + 1,
            title=act["title"],
            time=act["time"],
            iconBg=act["iconBg"],
            iconColor=act["iconColor"],
            badge=act["badge"]
        )
        for i, act in enumerate(raw_activities[:4])
    ]

    return DashboardStatsResponse(
        study_hours=study_hours_formatted,
        total_study_seconds=total_study_seconds,
        active_subjects_count=active_subjects_count,
        quiz_attempts_count=completed_attempts_count,
        competency_score=competency_score,
        competency_subtitle=competency_subtitle,
        weekly_hours_total=weekly_hours_total,
        weekly_data=weekly_data,
        continue_learning=continue_learning,
        recent_activities=recent_activities
    )
