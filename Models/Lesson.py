from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
from .Resource import lesson_resource_association

from sqlalchemy.orm import Session
import uuid

import Course
from ..database import Base

class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, primary_key=True)
    title = Column(String(length=100))
    index = Column(Integer)
    endpoint = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    data = Column(JSON)
    next_lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)
    next_lesson = relationship('Lesson', remote_side=[id], post_update=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)
    course = relationship('Course', back_populates='lessons')
    resources = relationship('Resource', secondary=lesson_resource_association, back_populates='lessons')

    def get_next_lesson(self, db: Session):
        return db.query(Lesson).filter(Lesson.id == self.next_lesson_id).first()

    def get_course(self, db: Session):
        return db.query(Course).filter(Course.id == self.course_id).first()


