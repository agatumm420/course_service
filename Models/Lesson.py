from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Session, relationship

from .base import Base
from .Component import Component, lesson_component_association
from .Course import Course
from .Resource import lesson_resource_association


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    title = Column(String(length=100))
    next_lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
    )
    position = Column(Integer, nullable=False, server_default=text("1"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    next_lesson = relationship(
        "Lesson",
        foreign_keys=[next_lesson_id],
        remote_side=[id],
        post_update=True,
    )
    course = relationship("Course", back_populates="lessons")
    lesson_data = relationship(
        "LessonData",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    components = relationship(
        Component,
        secondary=lesson_component_association,
        back_populates="lessons",
        order_by=lesson_component_association.c.position,
    )
    resources = relationship(
        "Resource",
        secondary=lesson_resource_association,
        back_populates="lessons",
    )

    def get_next_lesson(self, db: Session):
        return db.query(Lesson).filter(Lesson.id == self.next_lesson_id).first()

    def get_course(self, db: Session):
        return db.query(Course).filter(Course.id == self.course_id).first()
