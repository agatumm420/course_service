from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import relationship

from .base import Base


course_resource_association = Table(
    "course_resource",
    Base.metadata,
    Column(
        "course_id",
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "resource_id",
        Integer,
        ForeignKey("resources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_course_association = Table(
    "user_course",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("app_users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "course_id",
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False, server_default="")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    resources = relationship(
        "Resource",
        secondary=course_resource_association,
        back_populates="courses",
    )
    lessons = relationship("Lesson", back_populates="course")
    users = relationship(
        "User",
        secondary=user_course_association,
        back_populates="courses",
    )
    course_data = relationship(
        "CourseData",
        back_populates="course",
        cascade="all, delete-orphan",
    )
