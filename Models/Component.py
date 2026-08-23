from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base
from .ComponentField import ComponentField


lesson_component_association = Table(
    "lesson_component",
    Base.metadata,
    Column(
        "lesson_id",
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "component_id",
        Integer,
        ForeignKey("components.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("position", Integer, nullable=False),
    CheckConstraint("position > 0"),
    UniqueConstraint(
        "lesson_id",
        "position",
        name="uq_lesson_component_position",
        deferrable=True,
        initially="DEFERRED",
    ),
)


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    lessons = relationship(
        "Lesson",
        secondary=lesson_component_association,
        back_populates="components",
    )
    fields = relationship(
        ComponentField,
        back_populates="component",
        cascade="all, delete-orphan",
        order_by=ComponentField.id,
    )
