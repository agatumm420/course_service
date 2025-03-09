from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from Course import user_course_association
from ..database import Base
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100))

    courses = relationship('Course', secondary=user_course_association, back_populates='users')
    course_data = relationship('CourseData', back_populates='user') 