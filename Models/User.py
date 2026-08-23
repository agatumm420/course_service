from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.orm import relationship

from .base import Base
from .Course import user_course_association


class User(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False)
    provider = Column(Text)
    google_id = Column(Text, unique=True)
    apple_id = Column(Text, unique=True)
    password_hash = Column(Text)
    pin = Column(Text)
    status = Column(Integer)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    courses = relationship(
        "Course",
        secondary=user_course_association,
        back_populates="users",
    )
    course_data = relationship(
        "CourseData",
        back_populates="user",
        cascade="all, delete-orphan",
    )
