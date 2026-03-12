from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Quadrant(str, Enum):
    """Eisenhower quadrant enum"""

    Q1 = "Q1"  # Urgent & Important
    Q2 = "Q2"  # Not Urgent & Important
    Q3 = "Q3"  # Urgent & Not Important
    Q4 = "Q4"  # Not Urgent & Not Important


class Priority(str, Enum):
    """Task priority enum"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    quadrant: Quadrant  # AI-classified, required on creation
    priority: Priority = Priority.MEDIUM
    estimated_duration: Optional[int] = Field(None, ge=15, le=480)  # in minutes
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    quadrant: Optional[Quadrant] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    quadrant: Optional[Quadrant] = None
    priority: Optional[Priority] = None
    estimated_duration: Optional[int] = Field(None, ge=15, le=480)
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskChain(BaseModel):
    """Represents a sequence of dependent tasks"""

    tasks: List[TaskResponse]
    total_duration_minutes: int
    earliest_start: datetime
    latest_end: datetime


class ConflictReport(BaseModel):
    task_id: str
    conflict_type: str  # "overlap", "resource_overload", "missed_deadline"
    description: str
    conflicting_tasks: List[str]
    suggested_resolution: Optional[str] = None


class ScheduleResponse(BaseModel):
    tasks: List[TaskResponse]
    conflicts: List[ConflictReport]
    unscheduled_tasks: List[str]
    total_duration_minutes: int
    schedule_metadata: dict


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
