
from sqlalchemy import Column, Integer, String, ForeignKey, Text, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
from ..database import Base
class LessonData(Base):
    __tablename__ = 'lesson_data'
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('lessons.id'))
    course_data_id = Column(Integer, ForeignKey('course_data.id')) 
    data = Column(JSON) 

    lesson = relationship("Lesson", backref="lesson_data")

    course_data = relationship("CourseData", back_populates="lesson_data")