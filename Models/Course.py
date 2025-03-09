from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base

user_course_association = Table('user_course', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    lessons = relationship('Lesson', back_populates='course', cascade="all, delete-orphan")
    users = relationship('User', secondary=user_course_association, back_populates='courses')

    