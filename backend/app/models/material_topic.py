from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class MaterialTopic(Base):
    __tablename__ = "material_topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("learning_materials.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    subject_code = Column(String(100), nullable=False, index=True)
    chapter_title = Column(String(255), nullable=False)
    chapter_order = Column(Integer, default=1, nullable=False)
    topic_title = Column(String(255), nullable=False)
    topic_summary = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, default=15, nullable=False)
    order_num = Column(Integer, default=1, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    material = relationship("LearningMaterial", back_populates="topics")

