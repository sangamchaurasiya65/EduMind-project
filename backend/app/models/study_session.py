from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)
    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    ended_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    duration_seconds = Column(Integer, default=0, nullable=False)
