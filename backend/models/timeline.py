from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    schedule_data = Column(Text, nullable=True)  # JSON string with full schedule

    # Relationships
    user = relationship("User", back_populates="timelines")
    tasks = relationship(
        "TimelineTask", back_populates="timeline", cascade="all, delete-orphan"
    )
