from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base
from Models.Course import course_resource_association

lesson_resource_association = Table('lesson_resource', Base.metadata,
    Column('lesson_id', Integer, ForeignKey('lessons.id')),
    Column('resource_id', Integer, ForeignKey('resources.id'))
)

class Resource(Base):
    __tablename__ = 'resources'
    id      = Column(Integer, primary_key=True)
    type    = Column(String)
    path    = Column(String)

    lessons  = relationship(
        'Lesson',
        secondary=lesson_resource_association,
        back_populates='resources'
    )
    courses  = relationship(
        'Course',
        secondary=course_resource_association,
        back_populates='resources'
    )
