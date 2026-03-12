from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class RelationshipTypeEnum(str, enum.Enum):
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"


class TaskChain(Base):
    __tablename__ = "task_chains"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    prerequisite_task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type = Column(String(20), default=RelationshipTypeEnum.DEPENDS_ON)

    # Relationships
    task = relationship("Task", back_populates="chains_as_task", foreign_keys=[task_id])
    prerequisite_task = relationship(
        "Task",
        back_populates="chains_as_prerequisite",
        foreign_keys=[prerequisite_task_id],
    )
