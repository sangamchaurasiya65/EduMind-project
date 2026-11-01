from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.topic_completion import TopicCompletion
from backend.app.schemas.subject import SubjectProgressResponse
from backend.app.schemas.auth import TopicToggleRequest
from backend.app.services.auth_service import get_current_user
from backend.app.services.profile_service import log_user_activity
from backend.app.services.subject_progress_service import (
    get_all_subjects_progress_for_user,
    get_active_subjects_for_user,
    compute_user_subject_progress,
    sync_subject_progress_record,
    get_or_create_subject_definition
)

router = APIRouter(prefix="/subjects", tags=["Subject Progress & Syllabus"])



@router.get(
    "/progress",
    response_model=List[SubjectProgressResponse],
    summary="Retrieve real per-subject progress for the authenticated student"
)
def get_user_subjects_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authentic, strictly user-isolated progress metrics for the student's subjects:
    - If user has no uploaded materials or study activity, returns an empty list [].
    - New subject with materials has 0% progress and 'Not Started' status.
    - Status: 0% = 'Not Started', 1-99% = 'In Progress', 100% = 'Completed'.
    - Current topic: 'Not started yet' until learning begins.
    - Materials count & last activity timestamp.
    """
    return get_all_subjects_progress_for_user(
        db,
        user_id=str(current_user.id)
    )


@router.get(
    "/user-list",
    summary="Retrieve list of enrolled subjects for dropdown selection in materials upload"
)
def get_user_subjects_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns compact subject metadata for all subjects the user currently has.
    """
    active_subjects = get_active_subjects_for_user(db, user_id=str(current_user.id))
    results = []
    for s in active_subjects:
        results.append({
            "id": s["id"],
            "code": s["code"],
            "name": s["name"],
            "color": s.get("color", "#4f46e5"),
            "bg": s.get("bg", "#eef2ff")
        })
    return results


@router.get(
    "/{slug}/progress",
    response_model=SubjectProgressResponse,
    summary="Retrieve detailed progress and chapter status for a specific subject"
)
def get_single_subject_progress(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns detailed real-time progress and chapter-by-chapter progression for a single subject.
    """
    subj_def = get_or_create_subject_definition(slug)
    data = compute_user_subject_progress(
        db,
        user_id=str(current_user.id),
        subject_def=subj_def
    )
    sync_subject_progress_record(db, user_id=str(current_user.id), subject_def=subj_def, progress_data=data)
    return data


@router.post(
    "/{slug}/topics/toggle",
    summary="Toggle completion status of a topic/chapter within a subject"
)
def toggle_subject_topic(
    slug: str,
    req: TopicToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Toggles completion of a topic for the authenticated student.
    When marked completed, logs a daily study activity for streak tracking.
    Returns the updated subject progress.
    """
    subj_def = get_or_create_subject_definition(slug)
    user_id_str = str(current_user.id)
    subject_code = subj_def["code"].strip().upper()
    topic_title = req.topic_title.strip()

    existing = db.query(TopicCompletion).filter(
        TopicCompletion.user_id == user_id_str,
        TopicCompletion.subject_code == subject_code,
        TopicCompletion.topic_title == topic_title
    ).first()

    if req.completed is False or (req.completed is None and existing):
        if existing:
            db.delete(existing)
            db.commit()
        is_completed = False
    else:
        if not existing:
            comp = TopicCompletion(
                user_id=user_id_str,
                subject_code=subject_code,
                topic_title=topic_title,
                completed_at=datetime.now(timezone.utc)
            )
            db.add(comp)
            db.commit()
        # Log study activity for streak
        log_user_activity(
            db,
            user_id=user_id_str,
            activity_type="topic_completed",
            details=f"Completed {topic_title} in {subj_def['name']}"
        )
        is_completed = True

    # Re-evaluate and sync subject progress
    updated_progress = compute_user_subject_progress(db, user_id=user_id_str, subject_def=subj_def)
    sync_subject_progress_record(db, user_id=user_id_str, subject_def=subj_def, progress_data=updated_progress)

    return {
        "success": True,
        "is_completed": is_completed,
        "topic_title": topic_title,
        "subject_progress": updated_progress
    }

