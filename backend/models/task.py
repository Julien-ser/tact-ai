from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class QuadrantEnum(str, enum.Enum):
    Q1 = "Q1"  # Urgent & Important
    Q2 = "Q2"  # Not Urgent & Important
    Q3 = "Q3"  # Urgent & Not Important
    Q4 = "Q4"  # Not Urgent & Not Important


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quadrant = Column(String(20), nullable=False)
    priority = Column(String(20), default=PriorityEnum.MEDIUM)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tasks")
    chains_as_task = relationship(
        "TaskChain",
        back_populates="task",
        cascade="all, delete-orphan",
        foreign_keys="TaskChain.task_id",
    )
    chains_as_prerequisite = relationship(
        "TaskChain",
        back_populates="prerequisite_task",
        foreign_keys="TaskChain.prerequisite_task_id",
        cascade="all, delete-orphan",
    )
    timelines = relationship(
        "TimelineTask", back_populates="task", cascade="all, delete-orphan"
    )
