from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .base import Base
from .Course import course_resource_association


lesson_resource_association = Table(
    "lesson_resource",
    Base.metadata,
    Column(
        "lesson_id",
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "resource_id",
        Integer,
        ForeignKey("resources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    path = Column(String)

    lessons = relationship(
        "Lesson",
        secondary=lesson_resource_association,
        back_populates="resources",
    )
    courses = relationship(
        "Course",
        secondary=course_resource_association,
        back_populates="resources",
    )
