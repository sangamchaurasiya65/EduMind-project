from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.database import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)  # 'topic_completed', 'material_opened', 'quiz_submitted', 'study_session'
    activity_date = Column(String(10), nullable=False, index=True)  # 'YYYY-MM-DD'
    details = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
