from sqlalchemy import JSON, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base


class LessonData(Base):
    __tablename__ = "lesson_data"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    data = Column(JSON, nullable=False)

    lesson = relationship("Lesson", back_populates="lesson_data")
