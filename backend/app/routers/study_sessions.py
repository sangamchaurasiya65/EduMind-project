from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.study_session import StudySession
from backend.app.models.user import User
from backend.app.schemas.study_session import (
    StudySessionStartRequest,
    StudySessionHeartbeatRequest,
    StudySessionResponse
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.subject_progress_service import update_subject_progress_for_event
from backend.app.services.profile_service import log_user_activity

router = APIRouter(prefix="/study-sessions", tags=["Study Sessions Tracking"])


SLUG_TO_CODE = {
    "data-structures": "CS301",
    "database-management": "CS303",
    "computer-networks": "CS305",
    "operating-systems": "CS304",
    "software-engineering": "CS302",
    "computer-organization": "CS302",
    "engineering-mathematics": "MA301",
    "mathematics": "MA301",
    "general-studies": "GEN101",
}


def normalize_subject_id(raw_id: Optional[str]) -> Optional[str]:
    if not raw_id:
        return None
    cleaned = raw_id.strip()
    return SLUG_TO_CODE.get(cleaned.lower(), cleaned.upper())


@router.post(
    "/start",
    response_model=StudySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an active study tracking session"
)
def start_study_session(
    request: StudySessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initializes a new real-time study session tied to the authenticated user.
    Session is associated with the optional subject ID / code.
    """
    normalized_sub = normalize_subject_id(request.subject_id)
    now_utc = datetime.now(timezone.utc)

    session = StudySession(
        user_id=str(current_user.id),
        subject_id=normalized_sub,
        started_at=now_utc,
        ended_at=now_utc,
        duration_seconds=0
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    if normalized_sub:
        try:
            update_subject_progress_for_event(
                db=db,
                user_id=str(current_user.id),
                subject_code_or_slug=normalized_sub
            )
        except Exception:
            pass

    try:
        log_user_activity(
            db=db,
            user_id=str(current_user.id),
            activity_type="study_session",
            details=f"Study Session: {normalized_sub or 'General'}"
        )
    except Exception:
        pass

    return session



@router.post(
    "/{session_id}/heartbeat",
    response_model=StudySessionResponse,
    summary="Record heartbeat for active study session"
)
def record_heartbeat(
    session_id: int,
    request: StudySessionHeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the duration of an ongoing study session.
    Enforces user ownership and safely increments active duration.
    """
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session {session_id} not found."
        )

    # User isolation check
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this study session."
        )

    now_utc = datetime.now(timezone.utc)
    delta = request.delta_seconds if (request.delta_seconds and 1 <= request.delta_seconds <= 120) else 30

    session.duration_seconds += delta
    session.ended_at = now_utc

    db.commit()
    db.refresh(session)
    return session


@router.post(
    "/{session_id}/stop",
    response_model=StudySessionResponse,
    summary="Stop/finalize an active study session"
)
def stop_study_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalizes the study session by setting the completion timestamp.
    """
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session {session_id} not found."
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to stop this study session."
        )

    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session
