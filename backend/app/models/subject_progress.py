from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from backend.app.database import Base


class SubjectProgress(Base):
    __tablename__ = "subject_progress"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    subject_code = Column(String(50), nullable=False, index=True)
    subject_slug = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="Not Started", nullable=False)  # 'Not Started', 'In Progress', 'Completed'
    progress_percent = Column(Integer, default=0, nullable=False)
    current_topic = Column(String(255), default="—", nullable=False)
    materials_count = Column(Integer, default=0, nullable=False)
    topics_completed = Column(Integer, default=0, nullable=False)
    total_topics = Column(Integer, default=6, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "subject_code", name="uq_user_subject_progress"),
    )
