from sqlalchemy import Column, Integer, String, ForeignKey, Text, create_engine, JSON
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base

class CourseData(Base):
    __tablename__ = 'course_data'
    id                = Column(Integer, primary_key=True)
    course_id         = Column(Integer, ForeignKey('courses.id',   ondelete='CASCADE'))
    user_id           = Column(Integer, ForeignKey('users.id',     ondelete='CASCADE'))
    current_lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)

    course      = relationship('Course',    back_populates='course_data')
    user        = relationship('User',      back_populates='course_data')
    lesson_data = relationship('LessonData',back_populates='course_data')

    current_lesson = relationship(
        'Lesson',
        foreign_keys=[current_lesson_id],
        uselist=False
    )

