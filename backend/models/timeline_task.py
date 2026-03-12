from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class TimelineTask(Base):
    __tablename__ = "timeline_tasks"

    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(
        Integer, ForeignKey("timelines.id", ondelete="CASCADE"), nullable=False
    )
    task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    timeline = relationship("Timeline", back_populates="tasks")
    task = relationship("Task", back_populates="timelines")

    __table_args__ = (
        UniqueConstraint("timeline_id", "task_id", name="uq_timeline_task"),
    )
