from sqlalchemy import Column, Integer, String, ForeignKey, Text, create_engine, JSON
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base

class CourseData(Base):
    __tablename__ = 'course_data'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    user_id = Column(Integer, ForeignKey('users.id'))  
    course = relationship('Course', back_populates='course_data')
    lesson_data = relationship('LessonData', back_populates='course_data')
    user = relationship('User', back_populates='course_data')  
