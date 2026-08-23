from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base


class CourseData(Base):
    __tablename__ = "course_data"

    id = Column(Integer, primary_key=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    course = relationship("Course", back_populates="course_data")
    user = relationship("User", back_populates="course_data")
