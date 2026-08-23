from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class ComponentField(Base):
    __tablename__ = "component_fields"

    id = Column(Integer, primary_key=True)
    component_id = Column(
        Integer,
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    value = Column(String)
    data = Column(JSON)

    component = relationship("Component", back_populates="fields")
