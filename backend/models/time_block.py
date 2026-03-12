from sqlalchemy import Column, Integer, ForeignKey, Time
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class DayOfWeekEnum(int, enum.Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class TimeBlock(Base):
    __tablename__ = "time_blocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Relationships
    user = relationship("User", back_populates="time_blocks")
