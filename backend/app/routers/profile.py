from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.topic_completion import TopicCompletion
from backend.app.schemas.auth import (
    ProfileUpdateRequest,
    PreferencesUpdateRequest,
    ActivityLogRequest,
    TopicToggleRequest,
    UserResponse
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.profile_service import (
    get_user_profile_data,
    log_user_activity,
    get_user_study_dates,
    calculate_study_streak
)

router = APIRouter(prefix="/profile", tags=["Learner Profile & Stats"])


@router.get(
    "",
    summary="Retrieve authenticated learner profile, preferences, and real activity statistics"
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns authentic profile data for the authenticated learner:
    - Real topics completed across real subjects (0 and 'No subjects yet' for new user)
    - Real quizzes completed and real average score (0 and 'No quizzes taken yet' for new user)
    - Real study streak calculated from logged activity dates (0 Days for new user)
    - Personal best only shown if longest streak > 0
    - Degree/Course and Academic Semester
    - Learning preferences
    """
    return get_user_profile_data(db, current_user)


@router.put(
    "",
    summary="Update student profile information (Full Name, Course, Semester, Role)"
)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Updates profile fields on the authenticated user record in SQLite.
    Guarantees persistence across page reloads and sessions.
    """
    if req.full_name is not None and req.full_name.strip():
        current_user.full_name = req.full_name.strip()

    if req.course is not None:
        clean_course = req.course.strip() if req.course.strip() else None
        current_user.course = clean_course
        if clean_course:
            current_user.role = f"{clean_course} Student"

    if req.semester is not None:
        clean_sem = req.semester.strip() if req.semester.strip() else None
        current_user.semester = clean_sem

    if req.role is not None and req.role.strip():
        current_user.role = req.role.strip()

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    # Return updated full profile payload
    return get_user_profile_data(db, current_user)


@router.put(
    "/preferences",
    summary="Update student learning preferences (Learning Style, Daily Goal, Preferred Subject)"
)
def update_preferences(
    req: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Saves student learning preferences to database for personalized study flow.
    """
    if req.learning_style is not None:
        current_user.learning_style = req.learning_style.strip() if req.learning_style.strip() else None

    if req.daily_goal is not None:
        current_user.daily_goal = req.daily_goal.strip() if req.daily_goal.strip() else None

    if req.preferred_subject is not None:
        current_user.preferred_subject = req.preferred_subject.strip() if req.preferred_subject.strip() else None

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    return get_user_profile_data(db, current_user)


@router.post(
    "/activity/log",
    summary="Log a real study activity for streak tracking (user_id + date)"
)
def record_activity(
    req: ActivityLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Logs an activity (topic padha / material khola / quiz diya / study session)
    for the authenticated user with today's date in SQLite.
    """
    entry = log_user_activity(
        db,
        user_id=str(current_user.id),
        activity_type=req.activity_type,
        details=req.details
    )
    dates = get_user_study_dates(db, user_id=str(current_user.id))
    cur_streak, max_streak = calculate_study_streak(dates)

    return {
        "success": True,
        "entry_id": entry.id,
        "activity_date": entry.activity_date,
        "activity_type": entry.activity_type,
        "current_streak": cur_streak,
        "longest_streak": max_streak
    }


@router.post(
    "/topics/toggle",
    summary="Mark a topic/chapter as completed or in-progress"
)
def toggle_topic_completion(
    req: TopicToggleRequest,
    subject_code: str = "GENERAL",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Marks a topic complete or incomplete.
    When marked complete, logs an activity for streak tracking.
    """
    user_id_str = str(current_user.id)
    clean_subj = subject_code.strip().upper()
    clean_title = req.topic_title.strip()

    existing = db.query(TopicCompletion).filter(
        TopicCompletion.user_id == user_id_str,
        TopicCompletion.subject_code == clean_subj,
        TopicCompletion.topic_title == clean_title
    ).first()

    if req.completed is False or (req.completed is None and existing):
        # Remove completion
        if existing:
            db.delete(existing)
            db.commit()
            is_done = False
        else:
            is_done = False
    else:
        # Mark completed
        if not existing:
            comp = TopicCompletion(
                user_id=user_id_str,
                subject_code=clean_subj,
                topic_title=clean_title,
                completed_at=datetime.now(timezone.utc)
            )
            db.add(comp)
            db.commit()
        # Log study activity for streak
        log_user_activity(
            db,
            user_id=user_id_str,
            activity_type="topic_completed",
            details=f"Completed {clean_title} in {clean_subj}"
        )
        is_done = True

    return {
        "success": True,
        "topic_title": clean_title,
        "subject_code": clean_subj,
        "completed": is_done
    }
