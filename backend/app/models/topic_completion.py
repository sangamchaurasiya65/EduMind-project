from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from backend.app.database import Base


class TopicCompletion(Base):
    __tablename__ = "topic_completions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    subject_code = Column(String(50), nullable=False, index=True)
    topic_title = Column(String(255), nullable=False)
    completed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "subject_code", "topic_title", name="uq_user_topic_completion"),
    )
